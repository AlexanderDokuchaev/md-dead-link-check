from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Dict, List, Tuple

from git import Repo

RE_HEADER = r"^[#]{1,6}\s*(.*)"
RE_LINK = r"\[.*?\]\((.*?)\)"
RE_ID = r"<a\s+id=[\"'](.*)[\"']>.*?<\/a>"
RE_SUB = r"[$`][^`]+?[$`]"


@dataclass
class LinkInfo:
    link: str
    location: Path
    line_num: int

    def get_location(self) -> str:
        """
        Returns location link in format path:line
        """
        return f"{self.location}:{self.line_num}"

    def __lt__(self, other: LinkInfo) -> bool:
        return self.location < other.location or (self.location == other.location and self.line_num < other.line_num)


@dataclass
class MarkdownInfo:
    path: Path
    fragments: List[str] = field(default_factory=lambda: [])
    links: List[LinkInfo] = field(default_factory=lambda: [])


def find_all_markdowns_in_repo(repo: Repo) -> List[Path]:
    """
    Finds markdown file in current repository.
    """

    ret = []
    for file_path in repo.git.ls_files().splitlines():
        p = Path(file_path)
        if p.suffix == ".md":
            ret.append(p)
    return ret


def process_header_to_fragment(header: str) -> str:
    """
    Converts a Markdown header to a URL fragment.
    """

    header = header.strip()
    fragment = header.lower().replace(" ", "-")
    fragment = re.sub(r"[^a-z0-9-_]", "", fragment)
    return fragment


def process_md_file(path: Path, root_dir: Path) -> MarkdownInfo:
    fragments: List[str] = []
    links: List[LinkInfo] = []
    with (root_dir / path).open() as stream:
        in_code_block = ""
        for line_num, line in enumerate(stream.readlines(), 1):
            striped_line = line.strip()
            # Skip code blocks that can be start ``` or ````
            res = re.match(r"^(`{3,4})", striped_line)
            if res and not in_code_block:
                in_code_block = res.group(1)
                continue
            if striped_line.startswith(in_code_block):
                in_code_block = ""
            if in_code_block:
                continue

            # Skip $ and ` tags
            line = re.sub(RE_SUB, "", line)

            # Detect headers
            res = re.match(RE_HEADER, line)
            if res:
                fragment = process_header_to_fragment(res.group(1))
                fragments.append(fragment)
                continue

            # Detect links
            matches = re.findall(RE_LINK, line)
            if matches:
                for link in matches:
                    links.append(LinkInfo(link, path, line_num))

            # Detect id
            matches = re.findall(RE_ID, line)
            if matches:
                for id in matches:
                    fragments.append(id)
    return MarkdownInfo(path=path, fragments=fragments, links=links)


def preprocess_repository() -> Tuple[Dict[str, MarkdownInfo], Path]:
    repo = Repo(search_parent_directories=True)
    root_dir = Path(repo.working_dir)
    list_md_files = find_all_markdowns_in_repo(repo)
    md_data = {}
    for md_file in list_md_files:
        md_info = process_md_file(md_file, root_dir)
        md_data[md_file.as_posix()] = md_info
    return md_data, root_dir
