from pathlib import Path

import pytest
from git import Repo

from md_dead_link_check.preprocess import LinkInfo
from md_dead_link_check.preprocess import find_all_markdowns_in_repo
from md_dead_link_check.preprocess import process_header_to_fragment
from md_dead_link_check.preprocess import process_md_file


def test_find_all_markdowns_in_repo():
    repo = Repo(search_parent_directories=True)
    md_files = find_all_markdowns_in_repo(repo)
    refs = [
        "CHANGELOG.md",
        "README.md",
        "tests/test_md_files/a.md",
        "tests/test_md_files/b.md",
        "tests/test_md_files/d/a.md",
        "tests/test_md_files/fail.md",
    ]
    refs = [Path(r) for r in refs]
    assert refs == md_files


@pytest.mark.parametrize(
    "header, fragment",
    (
        ("1", "1"),
        ("Header 1", "header-1"),
        ("C++ ext", "c-ext"),
        ("H_I (H)", "h_i-h"),
        ("A `quotes` f", "a-quotes-f"),
    ),
)
def test_process_header_to_fragment(header, fragment):
    assert process_header_to_fragment(header) == fragment


def test_process_md_file():
    md_info = process_md_file(Path("tests/test_md_files/a.md"), Path(__file__).parent.parent)

    assert md_info.path == Path("tests/test_md_files/a.md")
    assert md_info.fragments == [
        "html-tag",
        "introduction",
        "code-block",
        "formula",
        "grave",
        "links",
        "header-with-quotes-and-math",
        "badge",
    ]

    ref_links = [
        LinkInfo(
            link="https://github.com/AlexanderDokuchaev",
            location=Path("tests/test_md_files/a.md"),
            line_num=27,
        ),
        LinkInfo(
            link="./b.md",
            location=Path("tests/test_md_files/a.md"),
            line_num=28,
        ),
        LinkInfo(
            link="b.md",
            location=Path("tests/test_md_files/a.md"),
            line_num=28,
        ),
        LinkInfo(
            link="./d/a.md",
            location=Path("tests/test_md_files/a.md"),
            line_num=29,
        ),
        LinkInfo(
            link="./d/a.md",
            location=Path("tests/test_md_files/a.md"),
            line_num=29,
        ),
        LinkInfo(
            link="/tests/test_md_files/d/a.md",
            location=Path("tests/test_md_files/a.md"),
            line_num=30,
        ),
        LinkInfo(
            link="https://github.com/AlexanderDokuchaev/md-dead-link-check/actions/workflows/github_action.yml/badge.svg?branch=main",
            location=Path("tests/test_md_files/a.md"),
            line_num=36,
        ),
        LinkInfo(
            link="https://github.com/AlexanderDokuchaev/md-dead-link-check/actions/workflows/github_action.yml",
            location=Path("tests/test_md_files/a.md"),
            line_num=36,
        ),
    ]
    assert md_info.links == ref_links
