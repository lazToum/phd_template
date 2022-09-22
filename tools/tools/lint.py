"""-*- coding: utf-8 -*-."""
import argparse
import os
import shutil
import sys
import timeit
from pathlib import Path

PYTHON_COMMANDS = [
    "isort",
    "black",
    "mypy",
    "flake8",
    "pylint",
    "bandit",
    "pydocstyle",
]
# LATEX_COMMANDS = ["chktex", "lacheck"]
LATEX_COMMANDS = ["chktex"]

ROOT = Path(__file__).parent.parent.resolve()

try:
    from .lib import DEFAULT_TEX_FILE, pip_install, run_command
except ImportError:
    sys.path.insert(0, str(ROOT))
    from tools.lib import DEFAULT_TEX_FILE, pip_install, run_command


def _lint_python():
    # type: () -> None
    pip_install(PYTHON_COMMANDS)
    for command in PYTHON_COMMANDS:
        config_file = str(ROOT.joinpath("pyproject.toml").resolve())
        if command == "flake8":
            config_file = ".flake8"
        if command == "isort":
            args = ""
        elif command == "pylint":
            args = f"--rcfile {config_file}"
        else:
            args = f"--config {config_file}"
        if command == "bandit":
            args += " -r"
        run_command(cwd=ROOT, command=f"{command} {args} tools")


def _lint_latex(file_path):
    # type: (Path) -> None
    for command in LATEX_COMMANDS:
        command_path = shutil.which(command)
        if command_path is None:
            print(f"Could not find {command}. Skipping...")
        else:
            args = []
            if command == "chktex":
                args.extend(["--localrc", "chktexrc"])
            run_command(
                cwd=ROOT.parent.resolve(),
                command=[command_path, str(file_path.name)] + args,
            )


def main():
    # type: () -> None
    """Run lint."""
    args = cli().parse_args()
    source_files = [args.files] if isinstance(args.files, str) else args.files
    for lang in source_files:
        if lang == "python":
            _lint_python()
        elif lang == "latex":
            file_path = Path(args.file).resolve()
            if not file_path.exists():
                # relative to parent dir?
                filename = file_path.name
                file_path = file_path.parent.parent.joinpath(
                    filename
                ).resolve()
            if not file_path.exists():
                msg = f"could not find the specified file {file_path}"
                raise FileNotFoundError(msg)
            _lint_latex(file_path)


def cli():
    # type: () -> argparse.ArgumentParser
    """Parse cli arguments."""
    parser = argparse.ArgumentParser(
        "", formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-f",
        "--file",
        required=False,
        type=Path,
        default=DEFAULT_TEX_FILE,
        help=f"Path to the main .tex file."
        f"\nDefault: ./{DEFAULT_TEX_FILE.name}",
    )
    parser.add_argument(
        "files",
        default="latex",
        nargs="*",
        choices=["latex", "python"],
        help="What file types to lint." "\nDefault: latex",
    )
    return parser


if __name__ == "__main__":
    tic = timeit.default_timer()
    main()
    toc = timeit.default_timer()
    print(f"{os.linesep}Done in {(toc - tic)} seconds{os.linesep}")
