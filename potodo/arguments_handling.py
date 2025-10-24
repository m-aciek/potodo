import argparse
import logging
import os
import sys
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path

from potodo import __version__


@dataclass
class Filters:
    """Store the filtering argument of potodo."""

    only_fuzzy: bool
    exclude_fuzzy: bool
    above: float
    below: float
    only_reserved: bool
    exclude_reserved: bool


def handle_dash_p_compat(args: argparse.Namespace) -> None:
    """Could be removed in like 2028.

    potodo had no position parameters, and I always forgot to type
    `-p` to give a path. So now potodo accepts paths as positional
    arguments :]
    """

    if args.old_paths:
        print(
            "🍰 hint: using -p to invoke potodo became optional in potodo 0.3.\n"
            "         (and may be removed in the future)",
            file=sys.stderr,
        )
    args.paths = args.old_paths + args.paths
    del args.old_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="potodo",
        description="List and prettify the po files left to translate.",
    )

    parser.add_argument(
        "-p",
        "--path",
        help="execute Potodo in path",
        metavar="path",
        action="append",
        default=[],
        dest="old_paths",
    )

    parser.add_argument(
        "paths",
        help="Examine files in given path(s)",
        nargs="*",
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
        "--no-color",
        action="store_true",
        help="Disable colored output.",
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
        "-s",
        "--show-finished",
        dest="show_finished",
        action="store_true",
        help="show files that are fully translated",
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
            "API URL to retrieve reservation tickets "
            "(https://api.github.com/repos/ORGANISATION/REPOSITORY/issues?state=open "
            "or "
            "https://git.afpy.org/api/v1/repos/ORGANISATION/REPOSITORY/issues?"
            "state=open&type=issues)"
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
        help="Suppress normal output; instead print the name of each matching po "
        "file from which output would normally "
        "have been printed.",
    )

    parser.add_argument(
        "--pot", help="Source template files path to compare the progress against"
    )

    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )

    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increases output verbosity"
    )

    # Initialize args and check consistency
    args = parser.parse_args()
    handle_dash_p_compat(args)
    check_args(args)

    args.filters = Filters(
        above=args.above,
        below=args.below,
        exclude_fuzzy=args.exclude_fuzzy,
        exclude_reserved=args.exclude_reserved,
        only_reserved=args.only_reserved,
        only_fuzzy=args.only_fuzzy,
    )
    return args


def check_args(args: Namespace) -> None:
    # If below is lower than above, raise an error
    if args.below < args.above:
        print(
            "Potodo: 'below' value must be greater than 'above' value.", file=sys.stderr
        )
        sys.exit(1)

    if args.json_format and args.is_interactive:
        print(
            "Potodo: Json format and interactive modes cannot be activated at the same time.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.is_interactive:
        try:
            import termios  # pylint: disable=unused-import
        except ImportError:
            import platform

            print(
                f'Potodo: "{platform.system()}" is not supported for interactive mode',
                file=sys.stderr,
            )
            sys.exit(1)

    if args.exclude_fuzzy and args.only_fuzzy:
        print(
            "Potodo: Cannot pass --exclude-fuzzy and --only-fuzzy at the same time.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.exclude_reserved and args.only_reserved:
        print(
            "Potodo: Cannot pass --exclude-reserved and --only-reserved at the same time.",
            file=sys.stderr,
        )
        sys.exit(1)

    # If no path is specified, use current directory
    if not args.paths:
        args.paths = [os.getcwd()]

    args.paths = [Path(path).resolve() for path in args.paths]

    try:
        levels = [logging.CRITICAL, logging.WARNING, logging.INFO, logging.DEBUG]
        args.logging_level = levels[args.verbose]
    except IndexError:
        print("Too many `-v`, what do you think you'll get?", file=sys.stderr)
        sys.exit(1)
