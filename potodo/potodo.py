import argparse
import json
import logging
from pathlib import Path
from typing import Any, Callable, List, Sequence

from gitignore_parser import rule_from_pattern

from potodo import __version__
from potodo.arguments_handling import check_args
from potodo.forge_api import get_issue_reservations
from potodo.json import json_dateconv
from potodo.logging import setup_logging
from potodo.po_file import PoDirectoryStats, PoFileStats, PoProjectStats


def print_dir_stats(
    directory: PoDirectoryStats,
    buffer: Sequence[str],
    printed_list: Sequence[bool],
) -> None:
    """This function prints the directory name, its stats and the buffer"""
    if True in printed_list:
        logging.debug("Printing directory %s", directory.path)
        # If at least one of the files isn't done then print the
        # folder stats and file(s) Each time a file is went over True
        # or False is placed in the printed_list list.  If False is
        # placed it means it doesnt need to be printed

        folder_completion = 100 * directory.translated / directory.total

        print(f"\n\n# {directory.path.name} ({folder_completion:.2f}% done)\n")
        print("\n".join(buffer))
    logging.debug("Not printing directory %s", directory.path)


def scan_path(
    path: Path,
    no_cache: bool,
    hide_reserved: bool,
    ignore_matches: Callable[[str], bool],
    api_url: str,
) -> PoProjectStats:
    logging.debug("Finding po files in %s", path)
    po_project = PoProjectStats(path, lambda file: not ignore_matches(file))
    cache_path = path.resolve() / ".potodo" / "cache.pickle"

    if no_cache:
        logging.debug("Creating PoFileStats objects for each file without cache")
    else:
        po_project.read_cache(cache_path)

    if not no_cache:
        po_project.write_cache(cache_path)

    if api_url and not hide_reserved:
        issue_reservations = get_issue_reservations(api_url)
        for po_file_stats in po_project.files.values():
            reserved_by, reservation_date = issue_reservations.get(
                po_file_stats.filename_dir.lower(), (None, None)
            )
            if reserved_by and reservation_date:
                po_file_stats.reserved_by = reserved_by
                po_file_stats.reservation_date = reservation_date

    return po_project


def non_interactive_output(
    path: Path,
    hide_reserved: bool,
    counts: bool,
    json_format: bool,
    select: Callable[[PoFileStats], bool],
    show_reservation_dates: bool,
    no_cache: bool,
    is_interactive: bool,
    matching_files: bool,
    ignore_matches: Callable[[str], bool],
    api_url: str,
) -> None:
    po_project = scan_path(path, no_cache, hide_reserved, ignore_matches, api_url)
    if json_format:
        print_po_project_as_json(
            po_project,
            counts,
            select,
            matching_files,
        )
    else:
        print_po_project(
            po_project,
            counts,
            select,
            matching_files,
        )


def print_po_project(
    po_project: PoProjectStats,
    counts: bool,
    select: Callable[[PoFileStats], bool],
    matching_files: bool,
) -> None:
    for directory in sorted(po_project.stats_by_directory()):
        # For each directory and files in this directory
        buffer: List[Any] = []
        printed_list: List[bool] = []

        for po_file in sorted(directory.files):
            # unless the offline/hide_reservation are enabled
            if not select(po_file):
                continue

            if matching_files:
                print(po_file.path)
                continue
            else:
                if counts:
                    buffer.append(po_file.counts())
                else:
                    buffer.append(po_file.percentages())

            # Indicate to print the file
            printed_list.append(True)

        # Once all files have been processed, print the dir and the files
        # or store them into a dict to print them once all directories have
        # been processed.
        print_dir_stats(directory, buffer, printed_list)

    if po_project.total != 0:
        total_completion = 100 * po_project.translated / po_project.total
        print(f"\n\n# TOTAL ({total_completion:.2f}% done)\n")


def print_po_project_as_json(
    po_project: PoProjectStats,
    counts: bool,
    select: Callable[[PoFileStats], bool],
    matching_files: bool,
) -> None:
    dir_stats: List[Any] = []
    for directory in sorted(po_project.stats_by_directory()):
        buffer: List[Any] = []
        for po_file in sorted(directory.files):
            if not select(po_file):
                continue
            buffer.append(po_file.as_dict())

        # Once all files have been processed, print the dir and the files
        # or store them into a dict to print them once all directories have
        # been processed.
        if buffer:
            folder_completion = 100 * directory.translated / directory.total
            dir_stats.append(
                {
                    "name": f"{directory.path.name}/",
                    "percent_translated": float(f"{folder_completion:.2f}"),
                    "files": buffer,
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


def exec_potodo(
    path: Path,
    exclude: List[str],
    hide_reserved: bool,
    counts: bool,
    json_format: bool,
    select: Callable[[PoFileStats], bool],
    show_reservation_dates: bool,
    no_cache: bool,
    is_interactive: bool,
    matching_files: bool,
    api_url: str,
) -> None:
    """
    Will run everything based on the given parameters

    :param path: The path to search into
    :param exclude: folders or files to be ignored
    :param hide_reserved: Will not show the reserved files
    :param counts: Render list with counts not percentage
    :param json_format: Format output as JSON.
    :param show_reservation_dates: Will show the reservation dates
    :param no_cache: Disables cache (Cache is disabled when files are modified)
    :param is_interactive: Switches output to an interactive CLI menu
    :param matching_files: Should the file paths be printed instead of normal output
    :param api_url: API URL for reservation tickets on Gitea or GitHub
    """

    ignore_matches = build_ignore_matcher(path, exclude)
    if is_interactive:
        from potodo.interactive import interactive_output

        interactive_output(path, ignore_matches)
    else:
        non_interactive_output(
            path,
            hide_reserved,
            counts,
            json_format,
            select,
            show_reservation_dates,
            no_cache,
            is_interactive,
            matching_files,
            ignore_matches,
            api_url,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="potodo",
        description="List and prettify the po files left to translate.",
    )

    parser.add_argument(
        "-p",
        "--path",
        help="execute Potodo in path",
        metavar="path",
    )

    parser.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        default=[],
        help="gitignore-style patterns to exclude from search.",
        metavar="path",
    )

    parser.add_argument(
        "-a",
        "--above",
        default=0,
        metavar="X",
        type=int,
        help="list all TODOs above given X%% completion",
    )

    parser.add_argument(
        "-b",
        "--below",
        default=100,
        metavar="X",
        type=int,
        help="list all TODOs below given X%% completion",
    )

    parser.add_argument(
        "-f",
        "--only-fuzzy",
        dest="only_fuzzy",
        action="store_true",
        help="print only files marked as fuzzys",
    )

    parser.add_argument(
        "-u",
        "--api-url",
        help=(
            "API URL to retrieve reservation tickets (https://api.github.com/repos/ORGANISATION/REPOSITORY/issues?state=open or https://git.afpy.org/api/v1/repos/ORGANISATION/REPOSITORY/issues?state=open&type=issues)"
        ),
    )

    parser.add_argument(
        "-n",
        "--no-reserved",
        dest="hide_reserved",
        action="store_true",
        help="don't print info about reserved files",
    )

    parser.add_argument(
        "-c",
        "--counts",
        action="store_true",
        help="render list with the count of remaining entries "
        "(translate or review) rather than percentage done",
    )

    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="json_format",
        help="format output as JSON",
    )

    parser.add_argument(
        "--exclude-fuzzy",
        action="store_true",
        dest="exclude_fuzzy",
        help="select only files without fuzzy entries",
    )

    parser.add_argument(
        "--exclude-reserved",
        action="store_true",
        dest="exclude_reserved",
        help="select only files that aren't reserved",
    )

    parser.add_argument(
        "--only-reserved",
        action="store_true",
        dest="only_reserved",
        help="select only only reserved files",
    )

    parser.add_argument(
        "--show-reservation-dates",
        action="store_true",
        dest="show_reservation_dates",
        help="show issue creation dates",
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        dest="no_cache",
        help="Disables cache (Cache is disabled when files are modified)",
    )

    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        dest="is_interactive",
        help="Activates the interactive menu",
    )

    parser.add_argument(
        "-l",
        "--matching-files",
        action="store_true",
        dest="matching_files",
        help="Suppress normal output; instead print the name of each matching po file from which output would normally "
        "have been printed.",
    )

    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )

    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increases output verbosity"
    )

    # Initialize args and check consistency
    args = parser.parse_args()
    check_args(args)

    def select(po_file: PoFileStats) -> bool:
        """Return True if the po_file should be displayed, False otherwise."""
        if args.only_fuzzy and not po_file.fuzzy_entries:
            return False
        if args.exclude_fuzzy and po_file.fuzzy_entries:
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

    if args.logging_level:
        setup_logging(args.logging_level)

    logging.info("Logging activated.")
    logging.debug("Executing potodo with args %s", args)

    # Launch the processing itself
    exec_potodo(
        args.path,
        args.exclude,
        args.hide_reserved,
        args.counts,
        args.json_format,
        select,
        args.show_reservation_dates,
        args.no_cache,
        args.is_interactive,
        args.matching_files,
        args.api_url,
    )
