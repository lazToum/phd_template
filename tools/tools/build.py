"""-*- coding: utf-8 -*-."""
import argparse
import itertools
import os
import shutil
import signal as signal_
import sys
import timeit
from collections import OrderedDict
from pathlib import Path
from types import FrameType
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()

OPTIONS = {
    "phase": ["proposal", "report", "thesis"],
    "language": ["english", "greek"],
    "status": ["draft", "final"],
}
PATTERNS = {
    "phase": "\\def\\Phase",
    "language": "\\def\\Language",
    "status": "\\def\\Status",
}

COMMAND_NAMES = ["xelatex", "biber"]

try:
    from .lib import (
        DEFAULT_BUILD_DIR,
        DEFAULT_OUTPUT_DIR,
        DEFAULT_TEX_FILE,
        backup,
        check_dependencies,
        detect,
        get_titles,
        get_user_id,
        pip_install,
        replace,
        restore,
        run_command,
    )
except ImportError:
    sys.path.insert(0, str(ROOT_DIR.joinpath("tools")))
    from tools.lib import (
        DEFAULT_BUILD_DIR,
        DEFAULT_OUTPUT_DIR,
        DEFAULT_TEX_FILE,
        backup,
        check_dependencies,
        detect,
        get_titles,
        get_user_id,
        pip_install,
        replace,
        restore,
        run_command,
    )


def _gather(file_path, run_all, **kwargs):
    # type: (Path, bool, Any) -> Dict[str, List[str]]
    items = {}  # type: Dict[str, List[str]]
    while kwargs:
        key, values = kwargs.popitem()
        if key not in items:
            items[key] = []
        if values == ["all"] or run_all:
            items[key].extend(OPTIONS[key])
        elif values == ["detect"]:
            detected = detect(file_path=file_path, keyword=PATTERNS[key])
            if detected:
                items[key].append(detected.replace("{", "").replace("}", ""))
            else:
                print(f"Could not detect {key}, building for all available.")
                items[key].extend(OPTIONS[key])
        else:
            items[key].extend(values)
    return OrderedDict({key: items[key] for key in sorted(items.keys())})


def _pre_build(file_path, build_dir, output_dir, **kwargs):
    # type: (Path, Path, Path, Any) -> None
    shutil.copyfile(file_path, str(file_path) + ".orig")
    pip_install(["pygmentize"])
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    patterns = [PATTERNS[arg] for arg in kwargs if arg in PATTERNS]
    substitutions = [
        f"{PATTERNS[key]}{{{value}}}"
        for key, value in kwargs.items()
        if key in PATTERNS
    ]
    replace(file_path, patterns=patterns, substitutions=substitutions)


def _post_build(file_path, build_dir, output_dir, current_titles, **kwargs):
    # type: (Path, Path, Path, List[str], Any) -> List[str]
    shutil.copyfile(str(file_path) + ".orig", file_path)
    os.remove(str(file_path) + ".orig")
    built_path = build_dir.joinpath(f"{file_path.stem}.pdf")
    _kwargs = {key: value for key, value in kwargs.items() if key in PATTERNS}
    document_titles = get_titles(
        file_path=file_path,
        current_titles=current_titles,
        **_kwargs,
    )
    for document_title in document_titles:
        dest_path = output_dir.joinpath(f"{document_title}.pdf")
        shutil.copyfile(built_path, dest_path)
    return document_titles


def _build(file_path, build_dir):
    # type: (Path, Path) -> None
    backup(file_path)
    cwd = file_path.parent.resolve()
    lualatex_cmd = (
        f"{shutil.which('lualatex')}"
        f" -synctex=1"
        f" --shell-escape"
        f" --output-directory {str(build_dir)}"
        f" -interaction=nonstopmode"
        f" {str(file_path)}"
    )
    biber_cmd = (
        f"{shutil.which('biber')}"
        f" --output-directory {str(build_dir)}"
        f" {str(file_path.stem)}"
    )
    # build => bib => build again twice to make sure refs are correct
    commands = [lualatex_cmd, biber_cmd, lualatex_cmd, lualatex_cmd]
    for command in commands:
        try:
            run_command(cwd, command)
        except Exception as error:
            raise error
        finally:
            restore(file_path)


def _run(
    file_path,  # type: Path
    build_dir,  # type: Path
    output_dir,  # type: Path
    run_all,  # type: bool
    **kwargs,  # type: Any
):
    # type: (...) -> None
    document_titles = []  # type: List[str]
    items = _gather(file_path=file_path, run_all=run_all, **kwargs)
    keys, values = zip(*items.items())
    calls = [dict(zip(keys, v)) for v in itertools.product(*values)]
    for call in calls:
        _pre_build(
            file_path, build_dir=build_dir, output_dir=output_dir, **call
        )
        _build(
            file_path=file_path,
            build_dir=build_dir,
        )
        new_titles = _post_build(
            file_path,
            build_dir=build_dir,
            output_dir=output_dir,
            current_titles=document_titles,
            **call,
        )
        document_titles.extend(new_titles)


def docker_build(args):
    # type: (argparse.Namespace) -> None
    """Run this file inside docker."""
    build_args = []
    for key, value in args.__dict__.items():
        if key == "docker":
            continue
        if not isinstance(value, bool) or value is True:
            build_args.append(f"--{key.replace('_', '-')}")
        if isinstance(value, Path):
            container_path = str(value).replace(str(ROOT_DIR), "/workdir")
            build_args.append(container_path)
        elif isinstance(value, list):
            build_args.extend(value)
    docker_image = "texlive/texlive:latest"
    docker_args = f"docker run --rm --user {get_user_id()} -e HOME=/tmp"
    docker_args += f" --workdir /workdir -v {ROOT_DIR}:/workdir"
    docker_command = (
        "bash -c 'export PATH=/tmp/.local/bin:${PATH} &&"
        " curl https://bootstrap.pypa.io/get-pip.py"
        " -o get-pip.py && python3 get-pip.py && rm get-pip.py &&"
        " python3 tools/run.py --build "
    )
    docker_command += " ".join(build_args) + "'"
    command = f"{docker_args} {docker_image} {docker_command}"
    os.system(command)  # nosec  # noqa


def main():
    # type: () -> None
    """Parse cli args and run."""
    args = cli().parse_args()
    if args.docker:
        check_dependencies(["docker"])
        docker_build(args)
        return
    check_dependencies(COMMAND_NAMES)
    file_path = Path(args.file).resolve()
    if not file_path.exists():
        # relative to parent dir?
        filename = file_path.name
        file_path = file_path.parent.parent.joinpath(filename).resolve()
    if not file_path.exists():
        msg = f"could not find the specified file {file_path}"
        raise FileNotFoundError(msg)
    # pylint: disable=unused-argument
    def _signal_handler(signal, frame):  # noqa
        # type: (int, Optional[FrameType]) -> None
        restore(file_path)
        print("Got interrupt, exiting...")
        sys.exit(0)

    signal_.signal(signal_.SIGINT, _signal_handler)
    output_dir = Path(args.output_dir).resolve()
    build_dir = Path(args.build_dir).resolve()
    kwargs = {key: args.__dict__[key] for key in OPTIONS}
    _run(
        file_path,
        build_dir=build_dir,
        output_dir=output_dir,
        run_all=args.all,
        **kwargs,
    )


def cli():
    # type: () -> argparse.ArgumentParser
    """Parse cli arguments."""
    parser = argparse.ArgumentParser(
        "", formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--file",
        required=False,
        default=DEFAULT_TEX_FILE,
        type=Path,
        help=f"Path to the main .tex file."
        f"\nDefault: ./{DEFAULT_TEX_FILE.name}",
    )
    parser.add_argument(
        "--build-dir",
        required=False,
        default=DEFAULT_BUILD_DIR,
        type=Path,
        help=f"Output directory.\nDefault: ./{DEFAULT_BUILD_DIR.name}",
    )
    parser.add_argument(
        "--output-dir",
        required=False,
        default=DEFAULT_OUTPUT_DIR,
        type=Path,
        help=f"Output directory.\nDefault: ./{DEFAULT_OUTPUT_DIR.name}",
    )
    for key, values in OPTIONS.items():
        parser.add_argument(
            f"--{key}",
            nargs="+",
            required=False,
            default=["detect"],
            type=str,
            choices=values + ["detect", "all"],
            help=f"{key.capitalize()}{'(es)' if key.endswith('s') else '(s)'}"
            f" to use.\nAvailable {key}{'es' if key.endswith('s') else 's'}: "
            f"{' | '.join(values)} | detect | all."
            "\nDefault: detect from tex file.",
        )
    parser.add_argument(
        "--all",
        required=False,
        default=False,
        action="store_true",
        help=f"Alias for: "
        f"{' '.join([f'--{key} all' for key in OPTIONS])}."
        f" Overrides existing {' '.join([f'--{key}' for key in OPTIONS])}"
        " arguments if any.",
    )
    parser.add_argument(
        "--docker",
        required=False,
        default=False,
        action="store_true",
        help=f"Use docker image (texlive/texlive:latest) "
        f"instead of local texlive ({', '.join(COMMAND_NAMES)}).",
    )
    return parser


if __name__ == "__main__":
    tic = timeit.default_timer()
    main()
    toc = timeit.default_timer()
    print(f"{os.linesep}Done in {(toc - tic)} seconds{os.linesep}")
