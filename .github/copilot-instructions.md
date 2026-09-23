# Copilot Instructions for md-dead-link-check

Lightweight, fast CLI tool that finds broken links in Markdown files. Ships as a CLI
(`md-dead-link-check`), a GitHub Action ([action.yaml](../action.yaml)), and a pre-commit hook.
Python >= 3.10, `src/` layout, built with hatchling.

## Architecture & data flow

The canonical package is [src/md_dead_link_check/](../src/md_dead_link_check/). `main()` in
[__main__.py](../src/md_dead_link_check/__main__.py) wires everything in this order:

1. `preprocess_repository()` ([preprocess.py](../src/md_dead_link_check/preprocess.py)) — uses
   GitPython (`Repo(search_parent_directories=True)`, `repo.git.ls_files()`) to list **tracked**
   files, then regex-parses every `.md` into `MarkdownInfo(path, fragments, links)` where each
   link is a `LinkInfo(link, location, line_num)`. Markdown is parsed with `RE_*` regex constants
   at the top of the module — there is no Markdown AST library.
2. `get_config()` ([config.py](../src/md_dead_link_check/config.py)) — loads the
   `[tool.md_dead_link_check]` table from `pyproject.toml` into the `Config` dataclass via
   `tomllib` (py>=3.11) / `tomli` (py<3.11). Unknown keys and bad values raise `ValueError`.
3. `check_all_links()` ([link_checker.py](../src/md_dead_link_check/link_checker.py)) — two passes:
   - `check_web_links()`: async via `aiohttp` (`asyncio.run` + `ClientSession(trust_env=True)`).
     Tries `HEAD`, falls back to `GET` on 404. Per-domain throttling delays
     (`generate_delays_for_one_domain_links`). Only checks the `files` list passed in.
   - `check_path_links()`: resolves local file paths + `#fragment` anchors against `md_data` and
     the repo file list. **Always runs for all files**, regardless of the `files` argument.
4. `summary()` ([helpers.py](../src/md_dead_link_check/helpers.py)) — prints colored/emoji output
   and returns the error count (becomes the process exit code).

`Status` is an `IntEnum` (`OK=0`, `WARNING=1`, `ERROR=2`); results sort by status then location.
Timeouts and uncaught HTTP codes are **WARNING** by default — only `catch_response_codes`
(`[404, 410, 500]`) become **ERROR**. Preserve this distinction when touching error handling.

## Project-specific conventions

- **One import per line.** Ruff isort runs with `force-single-line = true`; write
  `from x import a` / `from x import b` on separate lines, never `from x import a, b`.
- **Error-message variable (ruff `EM`).** Assign before raising:
  `msg = "..."` then `raise ValueError(msg)` — never `raise ValueError("...")` inline.
- **Modern typing.** `from __future__ import annotations`, builtin generics (`list[int]`,
  `dict[str, Any]`), `X | None`. mypy runs in `strict` mode (tests are excluded).
- **Dataclasses** for all data containers; mutable defaults use `field(default_factory=...)`.
- Line length is **120** (ruff). New parsing regexes go next to the other `RE_*` constants.
- User-facing config changes must be documented in [README.md](../README.md) and added to
  the `Config` dataclass + its validation in [config.py](../src/md_dead_link_check/config.py).

## Developer workflows

- Install dev env: `pip install .[dev]`
- Run tests (matches CI): `pytest tests -rfs -vv`
- Run all linters/formatters: `pre-commit run -a` (ruff-check `--fix`, ruff-format, strict mypy,
  markdownlint, taplo for TOML, actionlint). CI mirrors this in
  [.github/workflows/precommit.yml](workflows/precommit.yml).
- Smoke-test the tool on this repo: `md-dead-link-check --all`
- Bumping the version means editing `version` in [pyproject.toml](../pyproject.toml), the
  `default` in [action.yaml](../action.yaml), README usage examples, and [CHANGELOG.md](../CHANGELOG.md).

## Testing patterns

Tests live in [tests/](../tests/) (note the file name `test_link_cheker.py`). They use
`pytest.mark.parametrize` heavily and `pytest-mock` (`MockerFixture`). Network is never hit:
an `autouse` fixture patches `aiohttp.ClientSession.get`/`.head`. Fixture Markdown lives in
[tests/test_md_files/](../tests/test_md_files/); `fail.md` is the intentional-failure fixture and
is excluded via `exclude_files` in [pyproject.toml](../pyproject.toml). When adding parsing
behavior, extend the expected `fragments`/`LinkInfo` lists in
[test_preprocess.py](../tests/test_preprocess.py).
