from __future__ import annotations

import asyncio
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Optional
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


async def process_link(link_info: LinkInfo, session: ClientSession, timeout: int) -> StatusInfo:
    """
    Asynchronously processes a link to check its status and gather information.
    Timeout is not interpolated as error, because timeout often occur due to temporary server issues and
    retrying the request might be more appropriate than treating it as an immediate failure.
    """
    try:
        response = await session.head(link_info.link, allow_redirects=True, timeout=timeout, ssl=False)
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
    async with ClientSession(trust_env=True) as session:
        ret = await asyncio.gather(*[process_link(li, session, config.timeout) for li in links])
    return ret


def check_web_links(md_data: Dict[str, MarkdownInfo], config: Config, files: List[str]) -> List[StatusInfo]:
    web_links = []
    for md_file in files:
        if md_file not in md_data:
            continue
        md_file_info = md_data[md_file]
        if any(fnmatch(md_file, p) for p in config.exclude_files):
            continue
        for li in md_file_info.links:
            if any(fnmatch(li.link, p) for p in config.exclude_links):
                continue
            if urlsplit(li.link).netloc:
                web_links.append(li)

    return asyncio.run(async_check_links(web_links, config))


def check_path_links(md_data: Dict[str, MarkdownInfo], root_dir: Path, config: Config) -> List[StatusInfo]:
    ret = []
    for md_file, md_file_info in md_data.items():
        if any(fnmatch(md_file, p) for p in config.exclude_files):
            continue
        md_abs_path = root_dir / md_file_info.path
        for md_link in md_file_info.links:
            for p in config.exclude_links:
                print(fnmatch(md_link.link, p), md_link.link, p)
            if any(fnmatch(md_link.link, p) for p in config.exclude_links):
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
                    ret.append(StatusInfo(md_link, "Path is not within git repository"))
                    continue

                if abs_path.as_posix() != abs_path.resolve().as_posix():
                    ret.append(StatusInfo(md_link, "Path is not within git repository"))
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
