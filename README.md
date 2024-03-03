# Markdown Dead Link Checker

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
File: tests/test_md_files/fail.md:8 • Link: /test/fail.md1 • Error: Path does not exist
File: tests/test_md_files/fail.md:9 • Link: fail.md1 • Error: Path does not exist
File: tests/test_md_files/fail.md:13 • Link: a.md#fail • Error: Not found fragment
❌ Found 5 dead links 🙀
```

## Performance

This tool utilizes asynchronous API calls and avoids downloading full web pages,
enabling it to process thousands links in several seconds.

## Proxy

This tool leverages your system's existing HTTP and HTTPS proxy configuration. It achieves this by trusting the environment variables that your operating system utilizes to define proxy settings. This functionality is enabled by the `aiohttp.ClientSession(trust_env=True)` option.
For further technical details, you can refer to the [aiohttp documentation](https://docs.aiohttp.org/en/stable/client_advanced.html#proxy-support)

## How to Use It

### Option 1: GitHub Actions

Add Github Action config to `.github/workflow/`

```yaml
jobs:
  md-dead-link-check:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: AlexanderDokuchaev/md-dead-link-check@latest
```

### Option 2: Pre-Commit

Adding to your `.pre-commit-config.yaml` to integrate in [pre-commit](https://pre-commit.com/) tool

```yaml
  - repo: https://github.com/AlexanderDokuchaev/md-dead-link-check
    rev: latest
    hooks:
      - id: md-dead-link-check
```

### Option 3: Install from pip

For direct use, install with pip and run:

```bash
pip install md-dead-link-check
md-dead-link-check
```

## Configuration

This tool seamlessly integrates with your project's `pyproject.toml` file for configuration.
To leverage a different file, invoke the `--config` option during execution.

- timeout: Specifies the maximum time (in seconds) to wait for web link responses. Default: `10` seconds.
- exclude_links: Accepts a list of links to exclude from checks. Default: `[]`.
- exclude_files: Accepts a list of files to exclude from checks. Default: `[]`.
- check_web_links: Toggle web link checks on or off. Set to `false` to focus solely on file-based links. Default: `true`.

[!TIP]
Leverage wildcard patterns ([fnmatch](https://docs.python.org/3/library/fnmatch.html) syntax) for flexible exclusions in both `exclude_links` and `exclude_files` lists.

```toml
[tool.md_dead_link_check]
timeout = 10
exclude_links = ["https://github.com/", "*localhost*"]
exclude_files = ["tests/test_md_files/fail.md", "tests/*"]
check_web_links = true
```
