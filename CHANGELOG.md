# Changelog

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
