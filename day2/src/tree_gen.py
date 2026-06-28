"""File system tree generator that respects .gitignore."""

from __future__ import annotations

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

try:
    import pathspec
except ImportError:
    pathspec = None  # type: ignore


# Default noise patterns when no .gitignore is found or use_gitignore is True
_DEFAULT_IGNORE_PATTERNS = [
    "node_modules/",
    "__pycache__/",
    ".git/",
    ".gitignore",
    ".gitattributes",
    "dist/",
    "build/",
    "*.egg-info/",
    "*.egg",
    ".venv/",
    "venv/",
    "env/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".tox/",
    ".DS_Store",
    "Thumbs.db",
    "*.pyc",
    "*.pyo",
]


class TreeGenerator:
    """Recursively scan a directory and produce a Markdown-formatted tree."""

    def __init__(
        self,
        root_path: str | Path,
        max_depth: Optional[int] = None,
        use_gitignore: bool = True,
    ):
        self.root_path = Path(root_path).resolve()
        if not self.root_path.is_dir():
            raise ValueError(f"Path does not exist or is not a directory: {self.root_path}")
        self.max_depth = max_depth
        self.use_gitignore = use_gitignore
        self._spec: Optional[pathspec.PathSpec] = None

        if self.use_gitignore:
            gitignore_path = self.root_path / ".gitignore"
            if gitignore_path.is_file():
                patterns = gitignore_path.read_text(encoding="utf-8").splitlines()
                self._spec = pathspec.PathSpec.from_lines("gitignore", patterns)
            else:
                # No .gitignore found — use built-in defaults
                self._spec = pathspec.PathSpec.from_lines("gitignore", _DEFAULT_IGNORE_PATTERNS)

    def scan(self) -> str:
        """Walk the directory tree and return a formatted Markdown string."""
        lines: list[str] = [self.root_path.name + ("/" if self.root_path != self.root_path.parent else "/")]
        self._walk(self.root_path, "", lines, depth=0)
        return "\n".join(lines) + "\n"

    def _should_ignore(self, rel_path: str, is_dir: bool) -> bool:
        """Check if a path should be ignored based on gitignore rules."""
        if self._spec is None:
            return False
        # pathspec needs forward slashes on all platforms
        normalized = rel_path.replace(os.sep, "/")
        # Append trailing slash for directory patterns to match gitignore semantics
        check_path = normalized + "/" if is_dir and not normalized.endswith("/") else normalized
        return self._spec.match_file(check_path)

    def _walk(self, directory: Path, prefix: str, lines: list[str], depth: int):
        """Recursively walk a directory and build tree lines."""
        if self.max_depth is not None and depth >= self.max_depth:
            if prefix:
                lines.append(f"{prefix}...")
            return

        try:
            entries = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            lines.append(f"{prefix}[permission denied]")
            return

        # Filter ignored entries
        visible: list[tuple[str, bool]] = []
        for entry in entries:
            rel = str(entry.relative_to(self.root_path))
            is_dir = entry.is_dir(follow_symlinks=False)

            # Skip symlinks to directories (avoid cycles)
            if entry.is_symlink() and entry.is_dir():
                continue

            if self._should_ignore(rel, is_dir):
                continue

            visible.append((entry.name, is_dir))

        for i, (name, is_dir) in enumerate(visible):
            is_last = i == len(visible) - 1
            connector = "└── " if is_last else "├── "
            display = name + "/" if is_dir else name
            lines.append(f"{prefix}{connector}{display}")

            if is_dir:
                child_path = directory / name
                child_prefix = prefix + ("    " if is_last else "│   ")
                self._walk(child_path, child_prefix, lines, depth + 1)

    def _safe_write(self, content: str, output_path: str | Path, force: bool = False):
        """Write content to a file with overwrite protection and atomic write."""
        out = Path(output_path)
        if out.exists() and not force:
            raise FileExistsError(
                f"Output file already exists: {out}. Use --force to overwrite."
            )
        tmp_path = out.with_suffix(out.suffix + ".tmp")
        try:
            tmp_path.write_text(content, encoding="utf-8")
            os.replace(str(tmp_path), str(out))
        except Exception:
            # Clean up temp file on failure
            if tmp_path.exists():
                tmp_path.unlink()
            raise


def main():
    """CLI entry point."""
    # Fix Windows console encoding for tree-drawing characters
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="tree-gen",
        description="Generate a clean file system tree that respects .gitignore",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Save output to file instead of stdout",
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=None,
        help="Maximum recursion depth (default: unlimited)",
    )
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Disable .gitignore filtering and built-in noise filtering",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing output files",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="tree-gen 0.1.0",
    )

    args = parser.parse_args()

    try:
        generator = TreeGenerator(
            root_path=args.path,
            max_depth=args.depth,
            use_gitignore=not args.no_gitignore,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    tree_output = generator.scan()

    if args.output:
        try:
            generator._safe_write(tree_output, args.output, force=args.force)
        except FileExistsError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Wrap in Markdown code block when printing to terminal
        if sys.stdout.isatty():
            print("```text")
        print(tree_output, end="")
        if sys.stdout.isatty():
            print("```")


if __name__ == "__main__":
    main()
