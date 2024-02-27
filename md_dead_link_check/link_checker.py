from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
from urllib.parse import urlsplit

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectorError
from aiohttp.client_exceptions import ClientResponseError

from md_dead_link_check.config import Config
from md_dead_link_check.preprocess import LinkInfo
from md_dead_link_check.preprocess import MarkdownInfo

CATCH_RESPONSE_STATUS = [
    404,  # Not found
    500,  # Internal Server Error (for cannot connect to host under proxy)
]


@dataclass
class StatusInfo:
    link_info: LinkInfo
    err_msg: Optional[str] = None

    def __lt__(self, other: StatusInfo) -> bool:
        return self.link_info < other.link_info


def get_proxies(env: Mapping[str, Any]) -> Dict[str, Optional[str]]:
    """
    Find proxies in environment.
    """
    return {
        "http": env.get("http_proxy", env.get("HTTP_PROXY")),
        "https": env.get("https_proxy", env.get("HTTPS_PROXY")),
    }


def select_proxy(url: str, proxies: Dict[str, Optional[str]]) -> Optional[str]:
    """
    Select proxy setting by type by suffix of url.
    """
    if url.startswith("https://"):
        proxy = proxies.get("https")
    else:
        proxy = proxies.get("http")
    return proxy


async def process_link(
    link_info: LinkInfo, session: ClientSession, proxies: Dict[str, Optional[str]], timeout: int
) -> StatusInfo:
    """
    Asynchronously processes a link to check its status and gather information.
    Timeout is not interpolated as error, because timeout often occur due to temporary server issues and
    retrying the request might be more appropriate than treating it as an immediate failure.
    """
    try:
        proxy = select_proxy(link_info.link, proxies)
        headers = {"User-Agent": "Mozilla/5.0"}
        response = await session.head(
            link_info.link, allow_redirects=True, proxy=proxy, headers=headers, timeout=timeout
        )
        response.raise_for_status()
    except ClientResponseError as e:
        if e.status in CATCH_RESPONSE_STATUS:
            return StatusInfo(link_info, f"{e.status}: {e.message}")
    except asyncio.CancelledError as e:
        return StatusInfo(link_info, str(e))
    except ClientConnectorError as e:
        return StatusInfo(link_info, str(e))
    except asyncio.TimeoutError:
        pass

    return StatusInfo(link_info)


async def async_check_links(links: list[LinkInfo], config: Config) -> List[StatusInfo]:
    proxies = get_proxies(os.environ)
    async with ClientSession() as session:
        ret = await asyncio.gather(*[process_link(li, session, proxies, config.timeout) for li in links])
    return ret


def check_web_links(md_data: Dict[str, MarkdownInfo], config: Config, files: List[str]) -> List[StatusInfo]:
    web_links = []
    for md_file in files:
        if md_file not in md_data:
            continue
        md_file_info = md_data[md_file]
        if md_file in config.exclude_files:
            continue
        for li in md_file_info.links:
            if li.link in config.exclude_links:
                continue
            if urlsplit(li.link).netloc:
                web_links.append(li)

    return asyncio.run(async_check_links(web_links, config))


def check_path_links(md_data: Dict[str, MarkdownInfo], root_dir: Path, config: Config) -> List[StatusInfo]:
    ret = []
    for md_file, md_file_info in md_data.items():
        if md_file in config.exclude_files:
            continue
        md_abs_path = root_dir / md_file_info.path
        for md_link in md_file_info.links:
            if md_link.link in config.exclude_links:
                continue
            split_result = urlsplit(md_link.link)
            if split_result.netloc:
                continue
            fragment = split_result.fragment.lower()

            if not split_result.path:
                if fragment not in md_file_info.fragments:
                    ret.append(StatusInfo(md_link, "Not found header"))
                    continue
            else:
                try:
                    if split_result.path.startswith("/"):
                        # path from git root dir
                        abs_path = root_dir / split_result.path[1:]
                        res_path = Path(split_result.path[1:])
                    else:
                        abs_path = (md_abs_path.parent / split_result.path).resolve()
                        res_path = abs_path.relative_to(root_dir)
                except ValueError:
                    ret.append(StatusInfo(md_link, "Incorrect path"))
                    continue

                if res_path.as_posix() not in md_data:
                    if not abs_path.exists():
                        ret.append(StatusInfo(md_link, "Path does not exist"))
                    continue

                if fragment and fragment not in md_data[res_path.as_posix()].fragments:
                    ret.append(StatusInfo(md_link, "Not found fragment"))
                    continue
            ret.append(StatusInfo(md_link, None))
    return ret


def check_all_links(
    md_data: Dict[str, MarkdownInfo], config: Config, root_dir: Path, files: List[str]
) -> List[StatusInfo]:
    status_list: List[StatusInfo] = []
    if config.check_web_links:
        status_list.extend(check_web_links(md_data, config, files))
    status_list.extend(check_path_links(md_data, root_dir, config))
    return sorted(status_list)
