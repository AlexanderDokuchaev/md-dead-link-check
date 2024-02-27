# Markdown dead link checker

This is a lightweight and fast tool to help you keep your Markdown files free of broken links!
It scans your Markdown files and verifies whether each link is still active, letting you know if any need attention.

## Detection issues

- Unavailable web links.
- Incorrect links to file.
- Not existed fragments in markdown, like `[no-fragment](README.md#no-fragment)`.

Example of output for [fail.md](tests/test_md_files/fail.md)

```bash
File: tests/test_md_files/fail.md:3 • Link: https://github.com/AlexanderDokuchaev/FAILED • Error: 404: Not Found
File: tests/test_md_files/fail.md:4 • Link: https://not_exist_github.githubcom/ • Error: 500: Internal Server Error
File: tests/test_md_files/fail.md:8 • Link: /test/fail.md1 • Error: Path does not exist
File: tests/test_md_files/fail.md:9 • Link: fail.md1 • Error: Path does not exist
File: tests/test_md_files/fail.md:13 • Link: a.md#fail • Error: Not found fragment
❌ Found 5 dead links 🙀
```

## Usage

### Github action

```yaml
jobs:
  md-dead-link-check:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: AlexanderDokuchaev/md-dead-link-check@main
```

### Pre-commit hook

Adding to your .pre-commit-config.yaml

```yaml
  - repo: https://github.com/AlexanderDokuchaev/md-dead-link-check
    rev: main
    hooks:
      - id: md-dead-link-check
```

### Install rom pip

```bash
pip install md-dead-link-check
md-dead-link-check
```

### Install github repo

```bash
git clone https://github.com/AlexanderDokuchaev/md-dead-link-check
cd md-dead-link-check
pip install .
md-dead-link-check
```

## Configuration

By default use `pyproject.toml`, to use another config toml file use `--config`.

- timeout - timeout to response web link, defaults `10`.
- exclude_links - disable fails for links, defaults `[]`.
- exclude_files - disable check for file, defaults `[]`.
- check_web_links - to disable check web links, defaults `true`.

```toml
[tool.md_dead_link_check]
timeout = 10
exclude_links = ["https://github.com/"]
exclude_files = ["tests/test_md_files/fail.md"]
check_web_links = true
```
