from pathlib import Path

import pytest

from md_dead_link_check.config import Config
from md_dead_link_check.link_checker import MarkdownInfo
from md_dead_link_check.link_checker import StatusInfo
from md_dead_link_check.link_checker import check_all_links
from md_dead_link_check.link_checker import check_web_links
from md_dead_link_check.preprocess import LinkInfo
from md_dead_link_check.preprocess import process_md_file


@pytest.mark.parametrize(
    "url, msg",
    (
        ("https://github.com/AlexanderDokuchaev", None),
        ("https://github.com/AlexanderDokuchaev/FAILELINK", "404: Not Found"),
    ),
)
def test_check_link(url, msg):
    config = Config()
    data = {"test.md": MarkdownInfo("test.md", links=[LinkInfo(url, Path("test.md"), 0)])}
    [r] = check_web_links(data, config, ["test.md"])
    assert r.err_msg == msg


TEST_FILES = [Path("tests/test_md_files/fail.md"), Path("tests/test_md_files/a.md")]


def test_fails():
    path = "tests/test_md_files/fail.md"
    root_dir = Path(__file__).parent.parent
    md_data = {path: process_md_file(Path(path), root_dir)}
    ret = check_all_links(md_data, Config(), root_dir, list(md_data.keys()), TEST_FILES)

    # Output message depends on proxy settings
    ret[1].err_msg = None
    ret[1].warn_msg = None
    ret[7].err_msg = None
    ret[7].warn_msg = None
    ref = [
        StatusInfo(
            link_info=LinkInfo(
                link="https://github.com/AlexanderDokuchaev/FAILED",
                location=Path("tests/test_md_files/fail.md"),
                line_num=3,
            ),
            err_msg="404: Not Found",
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="https://not_exist_github.githubcom/",
                location=Path("tests/test_md_files/fail.md"),
                line_num=4,
            ),
            err_msg=None,
            warn_msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(link="/test/fail.md1", location=Path("tests/test_md_files/fail.md"), line_num=8),
            err_msg="Path not found",
        ),
        StatusInfo(
            link_info=LinkInfo(link="fail.md1", location=Path("tests/test_md_files/fail.md"), line_num=9),
            err_msg="Path not found",
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="/tests/test_md_files/fail.md#fail",
                location=Path("tests/test_md_files/fail.md"),
                line_num=13,
            ),
            err_msg="Fragment not found",
            warn_msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="not_exist_dir",
                location=Path("tests/test_md_files/fail.md"),
                line_num=15,
            ),
            err_msg="Path not found",
            warn_msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="error://urls/",
                location=Path("tests/test_md_files/fail.md"),
                line_num=17,
            ),
            err_msg="Unknown error",
            warn_msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="https://example.com/(bracket)",
                location=Path("tests/test_md_files/fail.md"),
                line_num=19,
            ),
            err_msg=None,
            warn_msg=None,
        ),
    ]
    assert ret == ref


def test_exclude_files():
    path = "tests/test_md_files/fail.md"
    root_dir = Path(__file__).parent.parent
    md_data = {path: process_md_file(Path(path), root_dir)}
    ret = check_all_links(md_data, Config(exclude_files=[path]), root_dir, [path], TEST_FILES)
    assert ret == []


@pytest.mark.parametrize(
    "exclude_links",
    (
        ["https://github.com/AlexanderDokuchaev/FAILED", "fail.md1", "/test/fail.md1"],
        ["https://github.com/AlexanderDokuchaev/*", "*.md1"],
    ),
    ids=["no_wildcard", "wildcard"],
)
def test_exclude_links(exclude_links):
    path = "tests/test_md_files/fail.md"
    root_dir = Path(__file__).parent.parent
    md_data = {path: process_md_file(Path(path), root_dir)}
    ret = check_all_links(
        md_data,
        Config(exclude_links=exclude_links),
        root_dir,
        list(md_data.keys()),
        TEST_FILES,
    )

    # Output message depends on proxy settings
    ret[0].err_msg = None
    ret[0].warn_msg = None
    ret[4].err_msg = None
    ret[4].warn_msg = None

    ref = [
        StatusInfo(
            link_info=LinkInfo(
                link="https://not_exist_github.githubcom/", location=Path("tests/test_md_files/fail.md"), line_num=4
            ),
            err_msg=None,
            warn_msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="/tests/test_md_files/fail.md#fail",
                location=Path("tests/test_md_files/fail.md"),
                line_num=13,
            ),
            err_msg="Fragment not found",
            warn_msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="not_exist_dir",
                location=Path("tests/test_md_files/fail.md"),
                line_num=15,
            ),
            err_msg="Path not found",
            warn_msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="error://urls/",
                location=Path("tests/test_md_files/fail.md"),
                line_num=17,
            ),
            err_msg="Unknown error",
            warn_msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="https://example.com/(bracket)",
                location=Path("tests/test_md_files/fail.md"),
                line_num=19,
            ),
            err_msg=None,
            warn_msg=None,
        ),
    ]
    assert ret == ref
