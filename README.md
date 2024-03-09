# Markdown Dead Link Checker

[![GitHub Action](https://github.com/AlexanderDokuchaev/md-dead-link-check/actions/workflows/github_action.yml/badge.svg?branch=main)](https://github.com/AlexanderDokuchaev/md-dead-link-check/actions/workflows/github_action.yml?query=branch%3Amain)
[![Ubuntu](https://github.com/AlexanderDokuchaev/md-dead-link-check/actions/workflows/ubuntu.yml/badge.svg?branch=main)](https://github.com/AlexanderDokuchaev/md-dead-link-check/actions/workflows/ubuntu.yml?query=branch%3Amain)
[![Windows](https://github.com/AlexanderDokuchaev/md-dead-link-check/actions/workflows/win.yml/badge.svg?branch=main)](https://github.com/AlexanderDokuchaev/md-dead-link-check/actions/workflows/win.yml?query=branch%3Amain)
[![MacOS](https://github.com/AlexanderDokuchaev/md-dead-link-check/actions/workflows/mac.yml/badge.svg?branch=main)](https://github.com/AlexanderDokuchaev/md-dead-link-check/actions/workflows/mac.yml?query=branch%3Amain)

This handy tool helps you maintain the integrity of your Markdown files by identifying broken links.
It scans your files and detects:

Here's what it does:

- Missing webpages: Links that no longer exist on the internet.
- Incorrect file links: Links that point to the wrong file in your project.
- Non-existent fragments (anchors): Links to specific sections that don't exist, e.g. `README.md#no-fragment`.

Example of output for [fail.md](tests/test_md_files/fail.md)

```bash
File: tests/test_md_files/fail.md:3 • Link: https://github.com/AlexanderDokuchaev/FAILED • Error: 404: Not Found
File: tests/test_md_files/fail.md:4 • Link: https://not_exist_github.githubcom/ • Error: 500: Internal Server Error
File: tests/test_md_files/fail.md:8 • Link: /test/fail.md1 • Error: Path does not exists in repository
File: tests/test_md_files/fail.md:9 • Link: fail.md1 • Error: Path does not exists in repository
File: tests/test_md_files/fail.md:13 • Link: /tests/test_md_files/fail.md#fail • Error: Not found fragment
File: tests/test_md_files/fail.md:15 • Link: not_exist_dir • Error: Path does not exists in repository
❌ Found 6 dead links 🙀
```

> [!NOTE]
> By defaults, only error codes like **404 (Not Found)**, **410 (Gone)**, and **500 (Internal Server Error)**,
> and links that don't exist are considered "dead links". Other error codes typically indicate
> temporary issues with the host server or unsupported links for the HEAD request type.

## How to Use It

### Option 1: GitHub Actions

Add Github Action config to `.github/workflow/`

```yaml
jobs:
  md-dead-link-check:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: AlexanderDokuchaev/md-dead-link-check@0.4
```

### Option 2: Pre-Commit

Adding to your `.pre-commit-config.yaml` to integrate in [pre-commit](https://pre-commit.com/) tool

```yaml
  - repo: https://github.com/AlexanderDokuchaev/md-dead-link-check
    rev: "0.4"
    hooks:
      - id: md-dead-link-check
```

### Option 3: Install from pip

For direct use, install with pip and run:

```bash
pip install md-dead-link-check
md-dead-link-check
```

## Performance

This tool utilizes asynchronous API calls and avoids downloading full web pages,
enabling it to process thousands links in several seconds.

## Proxy

This tool leverages your system's existing HTTP and HTTPS proxy configuration.
It achieves this by trusting the environment variables that your operating system utilizes to define proxy settings.
This functionality is enabled by the `aiohttp.ClientSession(trust_env=True)` option.
For further technical details, you can refer to the
[aiohttp documentation](https://docs.aiohttp.org/en/v3.9.3/client_advanced.html#proxy-support).

> [!WARNING]
> **Without proxy configuration in environment, link failures may not be reported.**
> If your environment lacks proxy configuration (variables like `http_proxy` and `https_proxy`),
> link retrieval attempts may time out without indicating a failure.
> To help diagnose this issue, use the `--warn` argument to log all processed links.

## Configuration

This tool seamlessly integrates with your project's `pyproject.toml` file for configuration.
To leverage a different file, invoke the `--config` option during execution.

- timeout: Specifies the maximum time (in seconds) to wait for web link responses. Default: `5` seconds.
- catch_response_codes: List of HTTP response codes to consider as failures.
If empty, all codes greater than 400 will be marked as failures. Default: `[404, 410, 500]`.
- exclude_links: List of links to exclude from checks. Default: `[]`.
- exclude_files: List of files to exclude from checks. Default: `[]`.
- force_get_requests_for_links: List of links for which the tool will use `GET` requests during checks. Default: `[]`.
- check_web_links: Toggle web link checks on or off. Default: `true`.
- validate_ssl: Toggles whether to validate SSL certificates when checking web links. Default: `true`.

> [!TIP]
> Leverage wildcard patterns ([fnmatch](https://docs.python.org/3/library/fnmatch.html) syntax) for
> `exclude_links`, `exclude_files` and `force_get_requests_for_links` parameters.

```toml
[tool.md_dead_link_check]
timeout = 5
exclude_links = ["https://github.com/", "https://github.com/*"]
exclude_files = ["tests/test_md_files/fail.md", "tests/*"]
check_web_links = true
catch_response_codes = [404, 410, 500]
force_get_requests_for_links = []
validate_ssl = true
```
