"""-*- coding: utf-8 -*-."""
import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

HERE = Path(__file__).parent.resolve()
try:
    from tools.lib import run_command
except ImportError:
    sys.path.insert(0, str(HERE))
    from tools.lib import run_command


def cli():
    # type: () -> argparse.ArgumentParser
    """Parse cli arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        help="Print this message and exit.",
    )
    parser.add_argument(
        "-l",
        "--lint",
        action="store_true",
        help="Lint source code.",
    )
    parser.add_argument(
        "-b",
        "--build",
        action="store_true",
        help="Build latex source.",
    )
    return parser


def _print_help(parser, args):
    if args.build:
        cmd = [sys.executable, '-m', "tools.build", "--help"]
        out = subprocess.check_output(cmd, cwd=HERE)
        build_help = out.decode()
        print(build_help)
    elif args.lint:
        cmd = [sys.executable, "-m", "tools.lint", "--help"]
        out = subprocess.check_output(cmd, cwd=HERE)
        lint_help = out.decode()
        print(lint_help)
    else:
        parser.print_help()
        print(
            "\nUse:\n  --help --build for build options"
            "\n  --help --lint for lint options"
        )


def _dir_paths(args):
    # type: (List[str]) -> List[str]
    _args = list(args)
    for key in ['--build-dir', '--output-dir']:
        if key in args and len(_args) > _args.index(key):
            value_index = _args.index(key) + 1
            dir_value = _args[value_index]
            if not os.path.isabs(dir_value):
                _args[value_index] = str(Path(dir_value).resolve())
    return _args


def main():
    # type: () -> None
    """Parse cli args and invoke command."""
    parser = cli()
    args, sub_args = parser.parse_known_args()
    no_args = not args.lint and not args.build
    if args.help or no_args:
        _print_help(parser=parser, args=args)
    elif args.build:
        build_args = _dir_paths(sub_args)
        command = [sys.executable, "-m", "tools.build"] + build_args
        run_command(cwd=HERE, command=command)
    else:
        command = [sys.executable, "-m", "tools.lint"] + sub_args
        run_command(cwd=HERE, command=command)


if __name__ == "__main__":
    main()
