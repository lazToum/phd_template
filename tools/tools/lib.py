"""-*- coding: utf-8 -*-."""
import itertools
import os
import pwd
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import mkstemp
from typing import Any, List, Optional, Union

_HERE = Path(__file__).parent.resolve()
DEFAULT_OUTPUT_DIR = _HERE.parent.parent.joinpath("dist")
DEFAULT_BUILD_DIR = _HERE.parent.parent.joinpath("build")
DEFAULT_TEX_FILE = _HERE.parent.parent.joinpath("main.tex")
TITLE_KEYWORD = "%FILE_NAME"
OUTPUTS_KEYWORD = "%MULTIPLE_OUTPUTS="


def get_user_id():
    # type: () -> int
    """Get the id of the user calling this function."""
    return pwd.getpwuid(os.getuid()).pw_uid


def backup(file_path):
    # type: (Path) -> None
    """Backup a file."""
    back_file = Path(str(file_path) + ".bak")
    back_file.unlink(missing_ok=True)
    shutil.copyfile(file_path, back_file)
    shutil.copymode(file_path, back_file)


def restore(file_path):
    # type: (Path) -> None
    """Restore a file."""
    back_file = Path(str(file_path) + ".bak")
    if back_file.exists():
        shutil.copymode(back_file, file_path)
        back_file.unlink(missing_ok=True)


def run_command(cwd, command):
    # type: (Path, Union[str, List[str]]) -> None
    """Run command."""
    if isinstance(command, list):
        _command = shlex.join(command)
    else:
        _command = command
    try:
        subprocess.check_call(
            shlex.split(_command),
            cwd=cwd,
            shell=False,
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as error:
        print(error)
        sys.exit(error.returncode)


def check_dependencies(commands):
    # type: (List[str]) -> None
    """Check if the desired `commands` can be found."""
    for command in commands:
        cmd_path = shutil.which(command)
        if cmd_path is None:
            msg = f"Could not find {command} in `PATH`. Is it installed?"
            raise FileNotFoundError(msg)


def pip_install(commands, force=False, upgrade=False):
    # type: (List[str], bool, bool) -> None
    """Install a python package (that has a cli) if it is not found."""
    for command in commands:
        if shutil.which(command) is None or force:
            args = "-m pip install"
            if force:
                args += " --force"
            if upgrade:
                args += " --upgrade"
            if command == "bandit":
                command += "[toml]"
            elif command == "pygmentize":
                command = "pygments"
            run_command(Path.cwd(), f"{sys.executable} {args} {command}")


def replace(file_path, patterns, substitutions):
    # type: (Path, List[str], List[str]) -> None
    """Credits: https://stackoverflow.com/a/39110."""
    if len(patterns) != len(substitutions):
        raise ValueError("Invalid number of patters/substitutions")
    file_handle, abs_path = mkstemp()
    with os.fdopen(file_handle, "w") as new_file:
        with open(file_path, "r", encoding="utf-8") as old_file:
            for line in old_file:
                if line.startswith(tuple(patterns)):
                    for index, pattern in enumerate(patterns):
                        if line.startswith(pattern):
                            sub = substitutions[index]
                            if not sub.endswith(os.linesep):
                                sub += os.linesep
                            new_file.write(sub)
                else:
                    new_file.write(line)
    shutil.copymode(file_path, abs_path)
    os.remove(file_path)
    shutil.move(abs_path, file_path)


def _find_possible_titles(excluded, **kwargs):
    # type: (List[str], Any) -> List[str]
    possible_titles = []
    args_count = len(list(kwargs.values()))
    for length in range(args_count, 0, -1):
        for combination in itertools.combinations(kwargs.values(), length):
            for permutation in itertools.permutations(combination):
                possible_title = "_".join(item for item in permutation)
                if possible_title not in excluded:
                    possible_titles.append(possible_title)
    return possible_titles


def detect(file_path, keyword):
    # type: (Path, str) -> Optional[str]
    """Detect value after keyword."""
    with open(file_path, "r", encoding="utf-8") as source_file:
        for line in source_file:
            if line.startswith(keyword):
                return line.split(keyword)[-1].rstrip()
    return None


def get_titles(file_path, current_titles, **kwargs):
    # type: (Path, List[str], Any) -> List[str]
    """Get the title of the document from the tex file."""
    titles = []  # type: List[str]
    multiple_out_string = detect(file_path, OUTPUTS_KEYWORD)
    multiple_outputs = False
    if multiple_out_string:
        multiple_outputs = multiple_out_string.lower() == "true"
    possible_titles = _find_possible_titles(current_titles, **kwargs)
    for possible_title in possible_titles:
        found_title = detect(file_path, f"{TITLE_KEYWORD}_{possible_title}=")
        if found_title and possible_title not in current_titles:
            titles.append(found_title)
            if not multiple_outputs:
                break
    if not titles or multiple_outputs:
        plain = detect(file_path, f"{TITLE_KEYWORD}=")
        if plain and plain not in current_titles:
            titles.append(plain)
    if not titles:
        # fallback: just use the language/phase/status ... as keys
        titles.append("_".join(value for value in kwargs.values()))
    return titles
