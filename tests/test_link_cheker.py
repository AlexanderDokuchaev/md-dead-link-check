from pathlib import Path

import pytest

from md_dead_link_check.config import Config
from md_dead_link_check.link_checker import MarkdownInfo
from md_dead_link_check.link_checker import StatusInfo
from md_dead_link_check.link_checker import check_all_links
from md_dead_link_check.link_checker import check_web_links
from md_dead_link_check.link_checker import get_proxies
from md_dead_link_check.preprocess import LinkInfo
from md_dead_link_check.preprocess import process_md_file


@pytest.mark.parametrize(
    "env, ref",
    (
        ({"http_proxy": "http", "https_proxy": "https"}, {"http": "http", "https": "https"}),
        ({"HTTP_PROXY": "http", "HTTPS_PROXY": "https"}, {"http": "http", "https": "https"}),
        ({"HTTP_PROXY": "http"}, {"http": "http", "https": None}),
        ({"HTTPS_PROXY": "https"}, {"http": None, "https": "https"}),
        ({}, {"http": None, "https": None}),
    ),
)
def test_get_proxies(env, ref):
    proxies = get_proxies(env)
    assert proxies == ref


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


def test_fails():
    path = "tests/test_md_files/fail.md"
    root_dir = Path(__file__).parent.parent
    md_data = {path: process_md_file(Path(path), root_dir)}
    ret = check_all_links(md_data, Config(), root_dir, list(md_data.keys()))

    # Differ err_msg on local test and github-ci
    ret[1].err_msg = ""

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
            err_msg="",
        ),
        StatusInfo(
            link_info=LinkInfo(link="/test/fail.md1", location=Path("tests/test_md_files/fail.md"), line_num=8),
            err_msg="Path does not exist",
        ),
        StatusInfo(
            link_info=LinkInfo(link="fail.md1", location=Path("tests/test_md_files/fail.md"), line_num=9),
            err_msg="Path does not exist",
        ),
    ]
    assert ret == ref


def test_exclude_files():
    path = "tests/test_md_files/fail.md"
    root_dir = Path(__file__).parent.parent
    md_data = {path: process_md_file(Path(path), root_dir)}
    ret = check_all_links(md_data, Config(exclude_files=[path]), root_dir, list(md_data.keys()))
    assert ret == []


@pytest.mark.parametrize(
    "exclude_links",
    (
        ["https://github.com/AlexanderDokuchaev/FAILED", "fail.md1", "/test/fail.md1"],
        ["https://github.com/AlexanderDokuchaev/*", "*.md1"],
    ),
    ids=["no_re", "re"],
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
    )

    # Differ err_msg on local test and github-ci
    ret[0].err_msg = ""

    ref = [
        StatusInfo(
            link_info=LinkInfo(
                link="https://not_exist_github.githubcom/",
                location=Path("tests/test_md_files/fail.md"),
                line_num=4,
            ),
            err_msg="",
        ),
    ]
    assert ret == ref
