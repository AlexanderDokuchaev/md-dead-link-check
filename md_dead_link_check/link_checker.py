from __future__ import annotations

import asyncio
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlsplit

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectorError
from aiohttp.client_exceptions import ClientResponseError

from md_dead_link_check.config import Config
from md_dead_link_check.preprocess import LinkInfo
from md_dead_link_check.preprocess import MarkdownInfo

TIMEOUT_RESPONSE_CODE = 408


@dataclass
class StatusInfo:
    link_info: LinkInfo
    err_msg: Optional[str] = None
    warn_msg: Optional[str] = None

    def __lt__(self, other: StatusInfo) -> bool:
        return self.link_info < other.link_info


@dataclass
class LinkStatus:
    link: str
    err_msg: Optional[str] = None
    warn_msg: Optional[str] = None


async def process_link(link: str, session: ClientSession, config: Config) -> LinkStatus:
    """
    Asynchronously processes a link to check its status and gather information.
    Timeout is not interpolated as error, because timeout often occur due to temporary server issues and
    retrying the request might be more appropriate than treating it as an immediate failure.
    """
    try:

        kwargs = {
            "url": link,
            "allow_redirects": True,
            "timeout": config.timeout,
            "ssl": config.validate_ssl,
        }
        if any(fnmatch(link, p) for p in config.force_get_requests_for_links):
            response = await session.get(**kwargs)
        else:
            response = await session.head(**kwargs)

        response.raise_for_status()
    except ClientResponseError as e:
        if not config.catch_response_codes or e.status in config.catch_response_codes:
            return LinkStatus(link, f"{e.status}: {e.message}")
        return LinkStatus(link, warn_msg=f"{e.status}: {e.message}")
    except asyncio.CancelledError as e:
        return LinkStatus(link, str(e))
    except ClientConnectorError as e:
        return LinkStatus(link, str(e))
    except asyncio.TimeoutError:
        if TIMEOUT_RESPONSE_CODE in config.catch_response_codes:
            return LinkStatus(link, err_msg="408: Timeout")
        return LinkStatus(link, warn_msg="408: Timeout")

    return LinkStatus(link)


async def async_check_links(links: Set[str], config: Config) -> List[LinkStatus]:
    async with ClientSession(trust_env=True) as session:
        ret = await asyncio.gather(*[process_link(li, session, config) for li in links])
    return ret


def check_web_links(md_data: Dict[str, MarkdownInfo], config: Config, files: List[str]) -> List[StatusInfo]:
    web_links: List[LinkInfo] = []
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

    # Check only unique links
    unique_links = set(li.link for li in web_links)
    links_status = asyncio.run(async_check_links(unique_links, config))
    links_status_dict = {li.link: li for li in links_status}

    ret = []
    for wl in web_links:
        li_status = links_status_dict[wl.link]
        ret.append(StatusInfo(wl, err_msg=li_status.err_msg, warn_msg=li_status.warn_msg))
    return ret


def check_path_links(
    md_data: Dict[str, MarkdownInfo], root_dir: Path, config: Config, files_in_repo: List[Path]
) -> List[StatusInfo]:
    ret = []
    for md_file, md_file_info in md_data.items():
        if any(fnmatch(md_file, p) for p in config.exclude_files):
            continue
        md_abs_path = root_dir / md_file_info.path
        for md_link in md_file_info.links:
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
                        rel_path = Path(split_result.path[1:])
                    else:
                        abs_path = (md_abs_path.parent / split_result.path).resolve()
                        rel_path = abs_path.relative_to(root_dir)
                except ValueError:
                    ret.append(StatusInfo(md_link, "Path is not within git repository"))
                    continue

                if abs_path.as_posix() != abs_path.resolve().as_posix():
                    ret.append(StatusInfo(md_link, "Path is not within git repository"))
                    continue

                if rel_path.as_posix() in md_data:
                    # Markdowns in repository
                    if fragment and fragment not in md_data[rel_path.as_posix()].fragments:
                        ret.append(StatusInfo(md_link, "Not found fragment"))
                        continue
                else:
                    # Not markdown file
                    if not any(f.is_relative_to(rel_path) for f in files_in_repo):
                        if rel_path.exists():
                            ret.append(StatusInfo(md_link, "File does not added to repository"))
                        else:
                            ret.append(StatusInfo(md_link, "Path does not exists in repository"))
                        continue

            ret.append(StatusInfo(md_link))
    return ret


def check_all_links(
    md_data: Dict[str, MarkdownInfo], config: Config, root_dir: Path, files: List[str], files_in_repo: List[Path]
) -> List[StatusInfo]:
    status_list: List[StatusInfo] = []
    if config.check_web_links:
        status_list.extend(check_web_links(md_data, config, files))
    status_list.extend(check_path_links(md_data, root_dir, config, files_in_repo))
    return sorted(status_list)
