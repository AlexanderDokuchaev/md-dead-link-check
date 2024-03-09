import os
import sys
from pathlib import Path
from typing import List

from md_dead_link_check.link_checker import StatusInfo


class SpecSymbols:
    __slots__ = ["blue", "green", "yellow", "red", "clean", "ok", "fail", "split", "cat_ok", "cat_fail"]

    def __init__(self) -> None:
        self.enable()

    def enable(self) -> None:
        self.blue = "\033[1;94m"
        self.green = "\033[1;92m"
        self.yellow = "\033[1;93m"
        self.red = "\033[1;91m"
        self.clean = "\033[0m"

        if sys.platform.startswith("win"):
            self.split = "-"
            self.ok = ""
            self.fail = ""
            self.cat_fail = ""
            self.cat_ok = ""
        else:
            self.split = "•"
            self.ok = "✅ "
            self.fail = "❌ "
            self.cat_fail = " 🙀"
            self.cat_ok = " 😸"

    def disable_colors(self) -> None:
        for key in self.__slots__:
            if key not in ["split"]:
                setattr(self, key, "")


def summary(status: List[StatusInfo], print_warn: bool, print_all: bool, no_color: bool) -> int:
    """
    Print summary.
    Returns 0 if not found any error, otherwise 1.
    """
    specs = SpecSymbols()
    if no_color:
        specs.disable_colors()
    err_nums = 0
    for x in status:
        link_msg = (
            f"{specs.blue}File:{specs.clean} {x.link_info.get_location()}"
            f" {specs.split} {specs.blue}Link:{specs.clean} {x.link_info.link}"
        )
        if x.err_msg:
            print(f"{link_msg} {specs.split} {specs.red}Error{specs.clean}: {x.err_msg}")
            err_nums += 1
        elif x.warn_msg and (print_warn or print_all):
            print(f"{link_msg} {specs.split} {specs.yellow}Warn{specs.clean}: {x.warn_msg}")
        elif print_all:
            print(f"{link_msg} {specs.split} {specs.green}OK{specs.clean}")

    if err_nums:
        cat_repeat = 0 if no_color else max(min(err_nums // 10, 5), 1)
        print(f"{specs.fail}Found {err_nums} dead link{'s' if err_nums >1 else ''}" + specs.cat_fail * cat_repeat)
        return 1
    else:
        print(f"{specs.ok}Not found dead links{specs.cat_ok}")
        return 0


def normalize_files(files: List[str], repo_dir: Path) -> List[str]:
    """
    Set file names to relative git root directory.
    """
    cwd = Path(os.getcwd())
    if cwd != repo_dir:
        return [(cwd / f).resolve().relative_to(repo_dir).as_posix() for f in files]
    return files
