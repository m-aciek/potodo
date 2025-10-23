import json
import logging
import shutil
from pathlib import Path
from tempfile import mkdtemp

import colorama
from colorama import Fore, Style

from potodo.arguments_handling import parse_args
from potodo.json import json_dateconv
from potodo.logging import setup_logging
from potodo.merge import sync_po_and_pot
from potodo.po_file import PoDirectories, PoDirectory


def print_matching_files(po_directories: PoDirectories, show_finished: bool) -> None:
    for po_directory in po_directories:
        for po_file in sorted(po_directory.files):
            if not show_finished and po_file.percent_translated == 100:
                continue
            print(po_file.path)


def _print_po_project(
    po_directory: PoDirectories | PoDirectory,
    counts: bool,
    show_reservation_dates: bool,
    show_finished: bool,
    prefix: str = "",
    last_one=False,
) -> None:
    if not po_directory.subdirectories and not po_directory.immediate_files:
        return
    if isinstance(po_directory, PoDirectories):
        n_dirs = len(po_directory.subdirectories)
        print(
            prefix
            + f"{n_dirs} director"
            + ("ies" if n_dirs > 1 else "y")
            + f"  {po_directory.completion:.2f}% done"
        )
    else:
        print(
            prefix
            + ("├── " if not last_one else "└── ")
            + f"{Fore.BLUE}{Style.BRIGHT}{po_directory.path.name}/{Style.RESET_ALL}"
            f"  {po_directory.completion:.2f}% done"
        )
        prefix += "    " if last_one else "│   "

    files_to_display = [
        file
        for file in po_directory.immediate_files
        if show_finished or file.percent_translated != 100
    ]
    for i, file_stat in enumerate(sorted(files_to_display)):
        last_one = i == len(files_to_display) - 1
        has_folders = len(po_directory.subdirectories)
        line = ""
        if counts:
            line += f"{file_stat.missing:3d} to do"
        else:
            line += f"{file_stat.translated:3d} / {file_stat.entries:3d}"
            line += f" ({file_stat.percent_translated:5.1f}% translated)"
        if file_stat.fuzzy:
            line += f", {file_stat.fuzzy} fuzzy"
        if file_stat.reserved_by is not None:
            line += ", " + file_stat.reservation_str(show_reservation_dates)
        mark = "└── " if last_one and not has_folders else "├── "
        print(f"{prefix + mark + file_stat.filename:<40} " + line)

    for i, directory in enumerate(po_directory.subdirectories):
        last_one = i == len(po_directory.subdirectories) - 1
        _print_po_project(
            directory, counts, show_reservation_dates, show_finished, prefix, last_one
        )


def print_po_project(
    po_directory: PoDirectories | PoDirectory,
    counts: bool,
    show_reservation_dates: bool,
    show_finished: bool,
    no_color: bool,
) -> None:
    if no_color:
        colorama.init(strip=True)
    else:
        colorama.init()
    _print_po_project(po_directory, counts, show_reservation_dates, show_finished)
    colorama.deinit()


def remove_finished_from_tree(tree):
    if "files" in tree:
        tree["files"] = [
            file for file in tree["files"] if file["percent_translated"] != 100
        ]
    for po_directory in tree["directories"]:
        remove_finished_from_tree(po_directory)


def print_po_project_as_json(
    po_directories: PoDirectories, show_finished: bool
) -> None:
    tree = po_directories.as_dict()
    if not show_finished:
        remove_finished_from_tree(tree)
    print(
        json.dumps(
            tree,
            indent=4,
            separators=(",", ": "),
            sort_keys=False,
            default=json_dateconv,
        )
    )


def main() -> None:
    args = parse_args()
    if args.logging_level:
        setup_logging(args.logging_level)

    logging.info("Logging activated.")
    logging.debug("Executing potodo with args %s", args)
    if args.pot:
        tmpdir = mkdtemp()
        po_directories = merge_and_scan_paths(
            args.paths,
            Path(args.pot),
            api_url=args.api_url,
            merge_path=Path(tmpdir),
        )
        if args.is_interactive:
            from potodo.interactive import interactive_output

            interactive_output(po_directories)
            return
    else:
        po_directories = PoDirectories.from_paths(args.paths)
        if args.is_interactive:
            from potodo.interactive import interactive_output

            interactive_output(po_directories)
            return
        if args.api_url:
            po_directories.fetch_issues(args.api_url)
    po_directories.filter(args.filters, args.exclude)
    if args.matching_files:
        print_matching_files(po_directories, args.show_finished)
    elif args.json_format:
        print_po_project_as_json(po_directories, args.show_finished)
    else:
        print_po_project(
            po_directories,
            args.counts,
            args.show_reservation_dates,
            args.show_finished,
            args.no_color,
        )
    if args.pot:
        shutil.rmtree(tmpdir)


def merge_and_scan_paths(
    paths: list[Path],
    pot_path: Path,
    merge_path: Path,
    api_url: str,
) -> PoDirectories:
    sync_po_and_pot(paths, pot_path, merge_path)
    directories = PoDirectories.from_paths([merge_path])
    if api_url:
        directories.fetch_issues(api_url)
    return directories
