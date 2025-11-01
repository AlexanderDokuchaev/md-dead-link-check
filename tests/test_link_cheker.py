from pathlib import Path

import pytest
from aiohttp import ClientResponseError
from aiohttp import RequestInfo
from aiohttp.client_exceptions import NonHttpUrlClientError
from pytest_mock import MockerFixture
from yarl import URL

from md_dead_link_check.config import Config
from md_dead_link_check.link_checker import LinkWithDelay
from md_dead_link_check.link_checker import MarkdownInfo
from md_dead_link_check.link_checker import Status
from md_dead_link_check.link_checker import StatusInfo
from md_dead_link_check.link_checker import check_all_links
from md_dead_link_check.link_checker import check_web_links
from md_dead_link_check.link_checker import generate_delays_for_one_domain_links
from md_dead_link_check.preprocess import LinkInfo
from md_dead_link_check.preprocess import process_md_file

ERROR_404 = [
    "https://github.com/AlexanderDokuchaev/FAILELINK",
    "https://github.com/AlexanderDokuchaev/FAILED",
    "https://example.com/(bracket)",
    "https://not_exist_github.githubcom/",
]
CLIENT_CONNECTION_ERROR = [
    "error://urls/",
]


class MockResponse:
    def __init__(self):
        self.status = 200
        self.reason = "OK"

    def raise_for_status(self):
        pass


@pytest.fixture(autouse=True)
def session_mock(mocker: MockerFixture) -> None:
    async def get_side_effect(url, *args, **kwargs):
        if url in ERROR_404:
            raise ClientResponseError(
                RequestInfo(url=url, method="GET", headers={}), (), status=404, message="Not Found"
            )
        if url in CLIENT_CONNECTION_ERROR:
            raise NonHttpUrlClientError(URL(url))
        return MockResponse()

    mocker.patch("aiohttp.ClientSession.get", side_effect=get_side_effect)
    mocker.patch("aiohttp.ClientSession.head", side_effect=get_side_effect)


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
    assert r.msg == msg


TEST_FILES = [Path("tests/test_md_files/fail.md"), Path("tests/test_md_files/a.md")]


def test_fails():
    path = "tests/test_md_files/fail.md"
    root_dir = Path(__file__).parent.parent
    md_data = {path: process_md_file(Path(path), root_dir)}
    ret = check_all_links(md_data, Config(), root_dir, list(md_data.keys()), TEST_FILES)

    # Output message depends on proxy settings
    ret[1].msg = None
    ret[1].status = None
    ret[7].msg = None
    ret[7].status = None
    ref = [
        StatusInfo(
            link_info=LinkInfo(
                link="https://github.com/AlexanderDokuchaev/FAILED",
                location=Path("tests/test_md_files/fail.md"),
                line_num=3,
            ),
            status=Status.ERROR,
            msg="404: Not Found",
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="https://not_exist_github.githubcom/",
                location=Path("tests/test_md_files/fail.md"),
                line_num=4,
            ),
            status=None,
            msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(link="/test/fail.md1", location=Path("tests/test_md_files/fail.md"), line_num=8),
            status=Status.ERROR,
            msg="Path not found",
        ),
        StatusInfo(
            link_info=LinkInfo(link="fail.md1", location=Path("tests/test_md_files/fail.md"), line_num=9),
            status=Status.ERROR,
            msg="Path not found",
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="/tests/test_md_files/fail.md#fail",
                location=Path("tests/test_md_files/fail.md"),
                line_num=13,
            ),
            status=Status.ERROR,
            msg="Fragment not found",
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="not_exist_dir",
                location=Path("tests/test_md_files/fail.md"),
                line_num=15,
            ),
            status=Status.ERROR,
            msg="Path not found",
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="error://urls/",
                location=Path("tests/test_md_files/fail.md"),
                line_num=17,
            ),
            status=Status.ERROR,
            msg="error://urls/",
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="https://example.com/(bracket)",
                location=Path("tests/test_md_files/fail.md"),
                line_num=19,
            ),
            msg=None,
            status=None,
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="https://example.com]https://example.com",
                location=Path("tests/test_md_files/fail.md"),
                line_num=21,
            ),
            status=Status.ERROR,
            msg="Error parsing link",
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
    ret[0].status = None
    ret[0].msg = None
    ret[4].status = None
    ret[4].msg = None

    ref = [
        StatusInfo(
            link_info=LinkInfo(
                link="https://not_exist_github.githubcom/", location=Path("tests/test_md_files/fail.md"), line_num=4
            ),
            status=None,
            msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="/tests/test_md_files/fail.md#fail",
                location=Path("tests/test_md_files/fail.md"),
                line_num=13,
            ),
            status=Status.ERROR,
            msg="Fragment not found",
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="not_exist_dir",
                location=Path("tests/test_md_files/fail.md"),
                line_num=15,
            ),
            status=Status.ERROR,
            msg="Path not found",
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="error://urls/",
                location=Path("tests/test_md_files/fail.md"),
                line_num=17,
            ),
            status=Status.ERROR,
            msg="error://urls/",
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="https://example.com/(bracket)",
                location=Path("tests/test_md_files/fail.md"),
                line_num=19,
            ),
            status=None,
            msg=None,
        ),
        StatusInfo(
            link_info=LinkInfo(
                link="https://example.com]https://example.com",
                location=Path("tests/test_md_files/fail.md"),
                line_num=21,
            ),
            status=Status.ERROR,
            msg="Error parsing link",
        ),
    ]
    assert ret == ref


def test_generate_delays_for_one_domain_links():
    links = ["https://example.com/1", "https://example.com/2", "https://example.com/3", "https://example2.com/1"]

    config = Config(throttle_groups=2, throttle_delay=10)
    ret = generate_delays_for_one_domain_links(links, config)
    assert ret == [
        LinkWithDelay("https://example.com/1", 0),
        LinkWithDelay("https://example.com/2", 0),
        LinkWithDelay("https://example.com/3", 10),
        LinkWithDelay("https://example2.com/1", 0),
    ]

    config = Config(throttle_groups=1, throttle_delay=100, throttle_max_delay=1000)
    ret = generate_delays_for_one_domain_links(links, config)
    assert ret == [
        LinkWithDelay("https://example.com/1", 0),
        LinkWithDelay("https://example.com/2", 100),
        LinkWithDelay("https://example.com/3", 200),
        LinkWithDelay("https://example2.com/1", 0),
    ]
