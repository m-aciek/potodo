import logging
import os
import sys
from argparse import Namespace
from pathlib import Path


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
            import termios  # noqa
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
    if not args.path:
        args.path = os.getcwd()

    args.path = Path(args.path).resolve()

    args.logging_level = None
    if args.verbose:
        if args.verbose == 1:
            # Will only show ERROR and CRITICAL
            args.logging_level = logging.WARNING
        if args.verbose == 2:
            # Will only show ERROR, CRITICAL and WARNING
            args.logging_level = logging.INFO
        if args.verbose >= 3:
            # Will show INFO WARNING ERROR DEBUG CRITICAL
            args.logging_level = logging.DEBUG
    else:
        # Disable all logging
        logging.disable(logging.CRITICAL)
