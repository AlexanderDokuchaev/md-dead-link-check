from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Dict, List, Tuple

from git import Repo

RE_HEADER = r"^(?:\s*[-+*]\s+|)[#]{1,6}\s*(.*)"
RE_LINK = r"([!]{0,1})\[([^\]!]*)\]\(([^()\s]+(?:\([^()\s]*\))*)\s*(.*?)\)"
RE_HTML_TAG = r"</?\w+[^>]*>"
RE_HTML_TAG_ID = r"<\w+\s+(?:[^>]*?\s+)?(?:id|name)=([\"'])(.*?)\1"
RE_HTML_TAG_HREF = r"<\w+\s+(?:[^>]*?\s+)?href=([\"'])(.*?)\1"
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

    fragment = header.strip()
    fragment = re.sub(RE_HTML_TAG, "", fragment)
    while True:
        res = re.search(RE_LINK, fragment)
        if not res:
            break
        if res.group(1) == "!":
            # Use # to work
            fragment = fragment.replace(res.group(0), "")
        else:
            fragment = fragment.replace(res.group(0), res.group(2))

    fragment = fragment.lower().replace(" ", "-")

    def filter_header_symbols(c: str) -> bool:
        return c.isalpha() or c.isdigit() or c in ["-", "_"]

    fragment = "".join(filter(filter_header_symbols, fragment))
    return fragment


def process_md_file(path: Path, root_dir: Path) -> MarkdownInfo:
    fragments: List[str] = []
    links: List[LinkInfo] = []
    with (root_dir / path).open(encoding="utf8") as stream:
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

            # Detect headers
            res = re.match(RE_HEADER, line)
            if res:
                _fragment = process_header_to_fragment(res.group(1))
                fragment = _fragment
                repeat = 0
                while fragment in fragments:
                    repeat += 1
                    fragment = f"{_fragment}-{repeat}"
                fragments.append(fragment)

            # Skip $ and ` tags
            line = re.sub(RE_SUB, "", line)

            # Detect links
            matches = re.findall(RE_LINK, line)
            for img_tag, text, link, title in matches:
                links.append(LinkInfo(link, path, line_num))

            if matches:
                # For case [![text](img_link)](link)
                sub_line = re.sub(RE_LINK, "link", line)
                matches2 = re.findall(RE_LINK, sub_line)
                for img_tag, text, link, title in matches2:
                    links.append(LinkInfo(link, path, line_num))

            # Detect id under a tag <a id="introduction"></a>
            matches = re.findall(RE_HTML_TAG_ID, line)
            for _, id in matches:
                fragments.append(id.lower())

            # Detect links under a tag <a href="introduction"></a>
            matches = re.findall(RE_HTML_TAG_HREF, line)
            for _, link in matches:
                links.append(LinkInfo(link, path, line_num))
    return MarkdownInfo(path=path, fragments=fragments, links=links)


def preprocess_repository() -> Tuple[Dict[str, MarkdownInfo], Path, List[Path]]:
    repo = Repo(search_parent_directories=True)
    root_dir = Path(repo.working_dir)
    list_md_files = find_all_markdowns_in_repo(repo)
    md_data = {}
    for md_file in list_md_files:
        md_info = process_md_file(md_file, root_dir)
        md_data[md_file.as_posix()] = md_info
    files_in_repo = [Path(x) for x in repo.git.ls_files().splitlines()]
    return md_data, root_dir, files_in_repo
