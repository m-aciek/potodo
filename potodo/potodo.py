import json
import logging
import shutil
from functools import partial
from pathlib import Path
from tempfile import mkdtemp
from typing import Callable, List

from gitignore_parser import handle_negation, rule_from_pattern

from potodo.arguments_handling import parse_args
from potodo.forge_api import get_issue_reservations
from potodo.json import json_dateconv
from potodo.logging import setup_logging
from potodo.merge import sync_po_and_pot
from potodo.po_file import PoFileStats, PoProjectStats


def scan_path(
    path: Path,
    no_cache: bool,
    hide_reserved: bool,
    api_url: str,
) -> PoProjectStats:
    logging.debug("Finding po files in %s", path)
    po_project = PoProjectStats(path)

    if no_cache:
        logging.debug("Creating PoFileStats objects for each file without cache")
    else:
        po_project.read_cache()

    po_project.rescan()

    if api_url and not hide_reserved:
        issue_reservations = get_issue_reservations(api_url)
        for po_file_stats in po_project.files:
            reserved_by, reservation_date = issue_reservations.get(
                po_file_stats.filename_dir.lower(), (None, None)
            )
            if reserved_by and reservation_date:
                po_file_stats.reserved_by = reserved_by
                po_file_stats.reservation_date = reservation_date
            else:  # Just in case we remember it's reserved from the cache:
                po_file_stats.reserved_by = None
                po_file_stats.reservation_date = None

    return po_project


def print_matching_files(po_project: PoProjectStats, show_finished: bool) -> None:
    for directory_stats in sorted(po_project.stats_by_directory()):
        for file_stat in sorted(directory_stats.files_stats):
            if not show_finished and file_stat.percent_translated == 100:
                continue
            print(file_stat.path)


def print_po_project(
    po_project: PoProjectStats,
    counts: bool,
    show_reservation_dates: bool,
    show_finished: bool,
) -> None:
    for directory_stats in sorted(po_project.stats_by_directory()):
        print(
            f"\n\n# {directory_stats.path.name} ({directory_stats.completion:.2f}% done)\n"
        )

        for file_stat in sorted(directory_stats.files_stats):
            if not show_finished and file_stat.percent_translated == 100:
                continue
            line = f"- {file_stat.filename:<30} "
            if counts:
                line += f"{file_stat.missing:3d} to do"
            else:
                line += f"{file_stat.translated:3d} / {file_stat.entries:3d}"
                line += f" ({file_stat.percent_translated:5.1f}% translated)"
            if file_stat.fuzzy:
                line += f", {file_stat.fuzzy} fuzzy"
            if file_stat.reserved_by is not None:
                line += ", " + file_stat.reservation_str(show_reservation_dates)
            print(line + ".")

    if po_project.entries != 0:
        print(f"\n\n# TOTAL ({po_project.completion:.2f}% done)\n")


def print_po_project_as_json(po_project: PoProjectStats, show_finished: bool) -> None:
    print(
        json.dumps(
            [
                {
                    "name": f"{directory_stats.path.name}/",
                    "percent_translated": directory_stats.completion,
                    "files": [
                        po_file.as_dict()
                        for po_file in sorted(directory_stats.files_stats)
                        if show_finished or po_file.percent_translated < 100
                    ],
                }
                for directory_stats in sorted(po_project.stats_by_directory())
            ],
            indent=4,
            separators=(",", ": "),
            sort_keys=False,
            default=json_dateconv,
        )
    )


def build_ignore_matcher(path: Path, exclude: List[str]) -> Callable[[str], bool]:
    potodo_ignore = path / ".potodoignore"
    rules = []
    if potodo_ignore.exists():
        for line in potodo_ignore.read_text().splitlines():
            rule = rule_from_pattern(line, path)
            if rule:
                rules.append(rule)
    rules.append(rule_from_pattern(".git/", path))
    for rule in exclude:
        rules.append(rule_from_pattern(rule, path))
    if not any(r.negation for r in rules):
        return lambda file_path: any(r.match(file_path) for r in rules)
    else:
        # We have negation rules. We can't use a simple "any" to evaluate them.
        # Later rules override earlier rules.
        return lambda file_path: handle_negation(file_path, rules)


def main() -> None:
    args = parse_args()

    if args.logging_level:
        setup_logging(args.logging_level)

    logging.info("Logging activated.")
    logging.debug("Executing potodo with args %s", args)

    ignore_matches = build_ignore_matcher(args.path, args.exclude)

    def select(ignore_matches: Callable[[str], bool], po_file: PoFileStats) -> bool:
        """Return True if the po_file should be displayed, False otherwise."""
        if ignore_matches(str(po_file.path)):
            return False
        if args.only_fuzzy and not po_file.fuzzy:
            return False
        if args.exclude_fuzzy and po_file.fuzzy:
            return False
        if (
            po_file.percent_translated < args.above
            or po_file.percent_translated > args.below
        ):
            return False

        # unless the offline/hide_reservation are enabled
        if args.exclude_reserved and po_file.reserved_by:
            return False
        if args.only_reserved and not po_file.reserved_by:
            return False

        return True

    if args.pot:
        tmpdir = mkdtemp()
        po_project = merge_and_scan_path(
            args.path,
            Path(args.pot),
            hide_reserved=args.hide_reserved,
            api_url=args.api_url,
            merge_path=Path(tmpdir),
        )
        ignore_matches = build_ignore_matcher(Path(tmpdir), args.exclude)

        if args.is_interactive:
            from potodo.interactive import interactive_output

            interactive_output(Path(tmpdir), ignore_matches)
            return
    else:
        if args.is_interactive:
            from potodo.interactive import interactive_output

            interactive_output(args.path, ignore_matches)
            return
        po_project = scan_path(
            args.path, args.no_cache, args.hide_reserved, args.api_url
        )
    po_project.filter(partial(select, ignore_matches))
    if args.matching_files:
        print_matching_files(po_project, args.show_finished)
    elif args.json_format:
        print_po_project_as_json(po_project, args.show_finished)
    else:
        print_po_project(
            po_project, args.counts, args.show_reservation_dates, args.show_finished
        )
    po_project.write_cache()
    if args.pot:
        shutil.rmtree(tmpdir)


def merge_and_scan_path(
    path: Path, pot_path: Path, merge_path: Path, hide_reserved: bool, api_url: str
) -> PoProjectStats:
    sync_po_and_pot(path, pot_path, merge_path)
    return scan_path(
        merge_path, no_cache=True, hide_reserved=hide_reserved, api_url=api_url
    )
