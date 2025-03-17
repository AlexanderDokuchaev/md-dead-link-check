# Changelog

## 1.2.0

- Use tomli (for python < '3.11) and tomllib (for python >= '3.11) instead of toml package (@szymonmaszke)
- Use ruff formatter for code instead of black and isort.
- Use commit hash instead of tag for version of actions.

## 1.1.0

- Add `--untrack` argument to check untracked files
- Detection bare links
- Add comments `<!-- md-dead-link-check: off -->` and `<!-- md-dead-link-check: on -->`
- Add message about applied throttling
- Add warning about detection "429: To Many Request"
- Drop support python3.8

## 1.0.0

- Added throttling to avoid hitting rate limits on external services.
- Filter `ftp` and `sftp` protocols for links.
- FIlter prefixes for the links like `mailto:`.
- Added `python_version` to the action inputs.
- Catch exception for `urllib.parse.urlsplit` in case of incorrect url.
- Added support `atx_closed` style of headers.
- Fix parsing one line code block with triple backticks.

## 0.9

- Support headers with links and html tags
- Support list of headers
- Support any langues
- Detect links with brackets
- Detect html tags with several arguments
- Fix crash on incorrect links

## 0.8

- Retry get request in case of head request return 404.

## 0.7

- Fixed github action to set not default config file.
- Updated readme of usage github actions.

## 0.6

- Github Action checks web link in changed files only for pull request events.
- Updated error messages.
- MIT license.

## 0.5

- Fixed converting header with link to fragment.
- Fixed parsing links for badge.
- Check same links only one time.
- Detection links to file that not added to repository.
- Added `warn` and `all` arguments.
- Removed `verbose` argument.

## 0.4

- Remove debug output

## 0.3

- Multi-platform support: Added support for Windows and macOS.
- Enhanced pre-commit hook: Set `always_run: True` for the pre-commit hook to ensure consistent detection of links to removed files before commit.
- Improved output: Added coloring to the output for better readability. Disable coloring with the --no-color argument.
- Verbose mode: Added the `--verbose` argument to display the status of all detected links, not just the first instance.
- Automatic proxy detection: Uses `trust_env=True` for `aiohttp.ClientSession` to automatically detect proxy settings.
- Extended configuration options:
  - Supports `fnmatch` syntax for pattern matching in configuration files.
  - Added new configuration options `force_get_requests_for_links`, `validate_ssl`, `catch_response_codes`.
- Detect relative links to files that is not within repository.
- Enhanced link detection: Improved detection of links in various formats, including:
  - `[![img](img_link)](link)`
  - `<a href="link"></a>`
  - `[text](link "title")`
