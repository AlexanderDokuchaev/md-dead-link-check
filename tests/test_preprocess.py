from dataclasses import dataclass
from pathlib import Path

import pytest

from md_dead_link_check.preprocess import LinkInfo
from md_dead_link_check.preprocess import detect_headers
from md_dead_link_check.preprocess import detect_links
from md_dead_link_check.preprocess import find_all_markdowns
from md_dead_link_check.preprocess import process_header_to_fragment
from md_dead_link_check.preprocess import process_md_file


def test_find_all_markdowns():
    files = [
        "md_dead_link_check/__init__.py",
        "tests/test_test.py",
        "action.yml",
        "CHANGELOG.md",
        "README.md",
    ]
    md_files = find_all_markdowns(files)
    refs = [
        "CHANGELOG.md",
        "README.md",
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
        ("H $ maths $", "h--maths-"),
        ("H [text](link)", "h-text"),
        ("H [![text](link)](link)", "h-"),
        ("🙀 header with icon", "-header-with-icon"),
        ("דוגמא", "דוגמא"),
        ("例子", "例子"),
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
        "badge-1",
        "badge-2",
        "some-link-link2",
        "some-tag-asd-",
        "id",
        "id2",
        "id3",
    ]

    ref_links = [
        LinkInfo(
            link="https://github.com/AlexanderDokuchaev",
            location=Path("tests/test_md_files/a.md"),
            line_num=27,
        ),
        LinkInfo(
            link="https://github.com",
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
            link="https://github.com",
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
        LinkInfo(
            link="#",
            location=Path("tests/test_md_files/a.md"),
            line_num=40,
        ),
        LinkInfo(
            link="./b.md#",
            location=Path("tests/test_md_files/a.md"),
            line_num=42,
        ),
        LinkInfo(
            link="#badge",
            location=Path("tests/test_md_files/a.md"),
            line_num=49,
        ),
        LinkInfo(
            link="#badge-1",
            location=Path("tests/test_md_files/a.md"),
            line_num=50,
        ),
        LinkInfo(
            link="#badge-2",
            location=Path("tests/test_md_files/a.md"),
            line_num=51,
        ),
        LinkInfo(
            link="b.md",
            location=Path("tests/test_md_files/a.md"),
            line_num=53,
        ),
        LinkInfo(
            link="b.md",
            location=Path("tests/test_md_files/a.md"),
            line_num=53,
        ),
        LinkInfo(
            link="mailto:example@example.example",
            location=Path("tests/test_md_files/a.md"),
            line_num=57,
        ),
        LinkInfo(
            link="mailto:example@example.example",
            location=Path("tests/test_md_files/a.md"),
            line_num=59,
        ),
        LinkInfo(
            link="ftp://example.example/example",
            location=Path("tests/test_md_files/a.md"),
            line_num=61,
        ),
        LinkInfo(
            link="https://github.com",
            location=Path("tests/test_md_files/a.md"),
            line_num=62,
        ),
        LinkInfo(
            link="https://github.com",
            location=Path("tests/test_md_files/a.md"),
            line_num=70,
        ),
        LinkInfo(
            link="https://github.com/",
            location=Path("tests/test_md_files/a.md"),
            line_num=70,
        ),
    ]
    assert md_info.links == ref_links


@dataclass
class HeaderTestCase:
    line: str
    header: str

    def __str__(self):
        return self.header


@pytest.mark.parametrize(
    "param",
    (
        HeaderTestCase("# 1", "1"),
        HeaderTestCase("## Header 1", "header-1"),
        HeaderTestCase("### Header 1", "header-1"),
        HeaderTestCase("#### Header 1", "header-1"),
        HeaderTestCase('<a id="head">', "head"),
        HeaderTestCase("# head<T>", "head"),
        HeaderTestCase("# head\<T\>", "headt"),
        HeaderTestCase("# h http://link", "h-httplink"),
        HeaderTestCase("# h <https://link>", "h-httpslink"),
        HeaderTestCase("# h <http://link.com/(ver)>", "h-httplinkcomver"),
        HeaderTestCase("# h <asd> ", "h-"),
        HeaderTestCase("# h \<asd\>", "h-asd"),
        HeaderTestCase("# h http://link <link> \<t\>   <http://link>", "h-httplink--t---httplink"),
    ),
    ids=str,
)
def test_detect_headers(param: HeaderTestCase):
    fragments = []
    detect_headers(param.line, fragments)
    assert param.header == fragments[0]


def test_same_header():
    fragments = []
    detect_headers("## Header", fragments)
    detect_headers("## Header", fragments)
    detect_headers("## Header", fragments)
    assert fragments == ["header", "header-1", "header-2"]


@pytest.mark.parametrize(
    "line, ref",
    (
        ("https://link", ["https://link"]),
        ("http://link", ["http://link"]),
        ("[1](link)", ["link"]),
        ("[1](<link>)", ["link"]),
        ("[1](<link with space>)", ["link with space"]),
        ("![1](link)", ["link"]),
        ("[![1](img)](link)", ["img", "link"]),
        ("[![1](<img>)](<link>)", ["img", "link"]),
        ("[![1](<img s>)](<link s>)", ["img s", "link s"]),
        ("link http://link and https://link2", ["http://link", "https://link2"]),
        ("<http://link>", ["http://link"]),
        ("<http://link(br)>", ["http://link(br)"]),
        ("[1](<http://link(br)>)", ["http://link(br)"]),
        ("[![1](<http://link(br)>)](link)", ["http://link(br)", "link"]),
    ),
)
def test_detect_links(line, ref):
    ret = detect_links(line)
    assert ret == ref
