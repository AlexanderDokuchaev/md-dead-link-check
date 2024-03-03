import os
from pathlib import Path
from typing import Dict, List

from md_dead_link_check.link_checker import StatusInfo


class Colors:
    def __init__(self) -> None:
        self.data: Dict[str, str] = {}
        self.enable()

    def __getattr__(self, attr: str) -> str:
        return self.data[attr]

    def enable(self) -> None:
        self.data["blue"] = "\033[1;94m"
        self.data["green"] = "\033[1;92m"
        self.data["yellow"] = "\033[1;93m"
        self.data["red"] = "\033[1;91m"
        self.data["clean"] = "\033[0m"

    def disable(self) -> None:
        for key in self.data:
            self.data[key] = ""


def summary(status: List[StatusInfo], verbose: bool, no_color: bool) -> int:
    """
    Print summary.
    Returns 0 if not found any error, otherwise 1.
    """
    color = Colors()
    if no_color:
        color.disable()
    err_nums = 0
    for x in status:
        link_msg = (
            f"{color.blue}File:{color.clean} {x.link_info.get_location()}"
            f" • {color.blue}Link:{color.clean} {x.link_info.link}"
        )
        if x.err_msg:
            print(f"{link_msg} • {color.red}Error{color.clean}: {x.err_msg}")
            err_nums += 1
        elif verbose:
            if x.warn_msg is None:
                print(f"{link_msg} • {color.green}OK{color.clean}")
            else:
                print(f"{link_msg} • {color.yellow}Warn{color.clean}: {x.warn_msg}")

    if err_nums:
        cat_repeat = 0 if no_color else max(min(err_nums // 10, 5), 1)
        print(f"❌ Found {err_nums} dead link{'s' if err_nums >1 else ''}" + " 🙀" * cat_repeat)
        return 1
    else:
        print("✅ Not found dead links 😸")
        return 0


def normalize_files(files: List[str], repo_dir: Path) -> List[str]:
    """
    Set file names to relative git root directory.
    """
    cwd = Path(os.getcwd())
    if cwd != repo_dir:
        return [(cwd / f).resolve().relative_to(repo_dir).as_posix() for f in files]
    return files
