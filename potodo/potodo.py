import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List

from gitignore_parser import rule_from_pattern

from potodo.arguments_handling import parse_args
from potodo.forge_api import get_issue_reservations
from potodo.json import json_dateconv
from potodo.logging import setup_logging
from potodo.po_file import PoFileStats, PoProjectStats


def scan_path(
    path: Path,
    no_cache: bool,
    hide_reserved: bool,
    api_url: str,
) -> PoProjectStats:
    logging.debug("Finding po files in %s", path)
    po_project = PoProjectStats(path)
    cache_path = path.resolve() / ".potodo" / "cache.pickle"

    if no_cache:
        logging.debug("Creating PoFileStats objects for each file without cache")
    else:
        po_project.read_cache(cache_path)

    po_project.rescan()

    if not no_cache:
        po_project.write_cache(cache_path)

    if api_url and not hide_reserved:
        issue_reservations = get_issue_reservations(api_url)
        for po_file_stats in po_project.files:
            reserved_by, reservation_date = issue_reservations.get(
                po_file_stats.filename_dir.lower(), (None, None)
            )
            if reserved_by and reservation_date:
                po_file_stats.reserved_by = reserved_by
                po_file_stats.reservation_date = reservation_date

    return po_project


def print_matching_files(po_project: PoProjectStats) -> None:
    for directory in sorted(po_project.stats_by_directory()):
        for po_file in sorted(directory.files):
            print(po_file.path)


def print_po_project(
    po_project: PoProjectStats, counts: bool, show_reservation_dates: bool
) -> None:
    for directory in sorted(po_project.stats_by_directory()):
        print(f"\n\n# {directory.path.name} ({directory.completion:.2f}% done)\n")

        for po_file in sorted(directory.files):
            line = f"- {po_file.filename:<30} "
            if counts:
                line += f"{po_file.missing:3d} to do"
            else:
                line += f"{po_file.translated:3d} / {po_file.entries:3d}"
                line += f" ({po_file.percent_translated:5.1f}% translated)"
            if po_file.fuzzy:
                line += f", {po_file.fuzzy} fuzzy"
            if po_file.reserved_by is not None:
                line += ", " + po_file.reservation_str(show_reservation_dates)
            print(line + ".")

    if po_project.entries != 0:
        print(f"\n\n# TOTAL ({po_project.completion:.2f}% done)\n")


def print_po_project_as_json(po_project: PoProjectStats) -> None:
    dir_stats: List[Dict[str, Any]] = []
    for directory in sorted(po_project.stats_by_directory()):
        dir_stats.append(
            {
                "name": f"{directory.path.name}/",
                "percent_translated": directory.completion,
                "files": [po_file.as_dict() for po_file in sorted(directory.files)],
            }
        )
    print(
        json.dumps(
            dir_stats,
            indent=4,
            separators=(",", ": "),
            sort_keys=False,
            default=json_dateconv,
        )
    )


def build_ignore_matcher(path: Path, exclude: List[str]) -> Callable[[str], bool]:
    path = path.resolve()
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
    return lambda file_path: any(r.match(file_path) for r in rules)


def main() -> None:
    args = parse_args()

    if args.logging_level:
        setup_logging(args.logging_level)

    logging.info("Logging activated.")
    logging.debug("Executing potodo with args %s", args)

    ignore_matches = build_ignore_matcher(args.path, args.exclude)

    def select(po_file: PoFileStats) -> bool:
        """Return True if the po_file should be displayed, False otherwise."""
        if ignore_matches(str(po_file.path)):
            return False
        if args.only_fuzzy and not po_file.fuzzy:
            return False
        if args.exclude_fuzzy and po_file.fuzzy:
            return False
        if (
            po_file.percent_translated == 100
            or po_file.percent_translated < args.above
            or po_file.percent_translated > args.below
        ):
            return False

        # unless the offline/hide_reservation are enabled
        if args.exclude_reserved and po_file.reserved_by:
            return False
        if args.only_reserved and not po_file.reserved_by:
            return False

        return True

    if args.is_interactive:
        from potodo.interactive import interactive_output

        interactive_output(args.path, ignore_matches)
        return

    po_project = scan_path(args.path, args.no_cache, args.hide_reserved, args.api_url)
    po_project.filter(select)
    if args.matching_files:
        print_matching_files(po_project)
    elif args.json_format:
        print_po_project_as_json(po_project)
    else:
        print_po_project(po_project, args.counts, args.show_reservation_dates)
