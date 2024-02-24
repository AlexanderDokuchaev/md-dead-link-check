import os
from argparse import ArgumentParser
from argparse import Namespace
from pathlib import Path
from typing import List

from md_dead_link_check.config import get_config
from md_dead_link_check.link_checker import StatusInfo
from md_dead_link_check.link_checker import check_all_links
from md_dead_link_check.preprocess import preprocess_repository


def summary(status: List[StatusInfo]) -> int:
    """
    Print summary.
    Returns 0 if not found any error, otherwise 1.
    """
    err_nums = 0
    for x in status:
        if x.err_msg:
            print(f"File: {x.link_info.get_location()} • Link: {x.link_info.link} • Error: {x.err_msg} ")
            err_nums += 1

    if err_nums:
        cat_repeat = max(min(err_nums // 10, 5), 1)
        print(f"❌ Found {err_nums} dead link{'s' if err_nums >1 else ''}" + " 🙀" * cat_repeat)
        return 1
    else:
        print("✅ Not found dead links 😸")
        return 0


def args_parser() -> Namespace:
    parser = ArgumentParser(description="Markdown dead link checker")
    parser.add_argument("--config", type=Path, help="Path to config file.")
    parser.add_argument("--hook", action="store_true", help="Run program in pre-commit hook.")
    parser.add_argument("files", nargs="*", help="List of file to check. If empty will check all markdown files.")
    return parser.parse_args()


def normalize_files(files: List[str], repo_dir: Path) -> List[str]:
    """
    Set file names to relative git root directory.
    """
    cwd = Path(os.getcwd())
    if cwd != repo_dir:
        return [(cwd / f).resolve().relative_to(repo_dir).as_posix() for f in files]
    return files


def main() -> int:
    args = args_parser()

    md_data, repo_dir = preprocess_repository()
    config = get_config(repo_dir, args.config)

    files = normalize_files(args.files, repo_dir)
    if not args.hook and not files:
        files = list(md_data)

    status_list = check_all_links(md_data, config, repo_dir, files)
    err_num = summary(status_list)

    return min(err_num, 1)


if __name__ == "__main__":
    raise SystemExit(main())
