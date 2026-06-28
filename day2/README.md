# tree-gen

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A clean file system tree generator that respects `.gitignore`. Recursively scan a directory and get a Markdown-formatted directory tree — perfect for README files, AI prompts, and team documentation.

## Why?

Running `tree` in a real project dumps everything — `node_modules/`, `__pycache__/`, `.git/`, `dist/` — hundreds of lines of noise for a project that only cares about source code. `tree-gen` reads your `.gitignore` and produces a **clean** tree automatically.

## Quick Start

```bash
pip install -r requirements.txt

# Scan current directory
python src/tree_gen.py .

# Save to file
python src/tree_gen.py ./my-project --output tree.md

# Limit depth
python src/tree_gen.py ./ --depth 2

# Show everything (ignore .gitignore)
python src/tree_gen.py ./ --no-gitignore
```

## Features

- **Smart filtering** — reads `.gitignore` automatically; falls back to built-in noise patterns
- **Markdown output** — clean tree-drawing characters (`├──`, `│`, `└──`), ready to paste anywhere
- **Depth control** — limit recursion with `--depth`
- **Overwrite protection** — refuses to clobber existing files unless you pass `--force`
- **Atomic writes** — writes to a temp file first, then renames (no partial output on crash)
- **Edge case handling** — skips symlinks, catches permission errors gracefully

## CLI Reference

| Argument | Description |
|----------|-------------|
| `path` | Directory to scan (default: `.`) |
| `-o, --output` | Save to file instead of stdout |
| `-d, --depth` | Max recursion depth (default: unlimited) |
| `--no-gitignore` | Disable all filtering |
| `-f, --force` | Overwrite existing output file |
| `--version` | Show version |

## Example Output

```text
wx/
├── examples/
├── src/
│   ├── __init__.py
│   └── tree_gen.py
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   └── test_tree_gen.py
├── .gitignore
├── pyproject.toml
└── requirements.txt
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

## License

MIT
