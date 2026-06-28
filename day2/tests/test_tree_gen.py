"""Unit tests for TreeGenerator core logic."""

import os
import tempfile
from pathlib import Path

import pytest

from src.tree_gen import TreeGenerator


def _create_tree(root: Path, structure: dict):
    """Create a directory tree from a nested dict.
    Dict values: None = file, dict = directory.
    """
    for name, content in structure.items():
        full = root / name
        if content is None:
            full.write_text("", encoding="utf-8")
        else:
            full.mkdir(parents=True, exist_ok=True)
            _create_tree(full, content)


class TestTreeGenerator:
    """Tests for the TreeGenerator class."""

    def test_basic_tree(self):
        """Verify basic tree structure with correct connectors."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _create_tree(root, {
                "src": {
                    "main.py": None,
                    "utils.py": None,
                },
                "tests": {
                    "test_main.py": None,
                },
                "README.md": None,
            })
            gen = TreeGenerator(root, use_gitignore=False)
            output = gen.scan()
            assert "├── src/" in output
            assert "│   ├── main.py" in output
            assert "│   └── utils.py" in output
            assert "├── tests/" in output
            assert "│   └── test_main.py" in output
            assert "└── README.md" in output

    def test_gitignore_filtering(self):
        """Verify .gitignore patterns exclude matching files/dirs."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("node_modules/\n__pycache__/\n", encoding="utf-8")
            _create_tree(root, {
                "node_modules": {
                    "pkg.js": None,
                },
                "src": {
                    "main.py": None,
                },
            })
            gen = TreeGenerator(root, use_gitignore=True)
            output = gen.scan()
            assert "node_modules" not in output
            assert "pkg.js" not in output
            assert "src/" in output
            assert "main.py" in output

    def test_gitignore_negation(self):
        """Verify ! negation rules work with pathspec matching."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Use a pattern + negation: ignore *.log but keep important.log
            (root / ".gitignore").write_text("*.log\n!important.log\n", encoding="utf-8")
            _create_tree(root, {
                "dist": {
                    "important.log": None,
                    "debug.log": None,
                },
                "src": {
                    "main.py": None,
                },
            })
            gen = TreeGenerator(root, use_gitignore=True)
            output = gen.scan()
            # important.log is negated back in
            assert "important.log" in output
            # debug.log is still ignored
            assert "debug.log" not in output
            # dist directory and its contents are not ignored
            assert "dist/" in output

    def test_depth_limiting(self):
        """Verify max_depth stops recursion and shows ... placeholder."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _create_tree(root, {
                "level1": {
                    "level2": {
                        "level3": {
                            "deep.py": None,
                        },
                    },
                },
            })
            gen = TreeGenerator(root, max_depth=2, use_gitignore=False)
            output = gen.scan()
            assert "level1/" in output
            assert "level2/" in output
            assert "..." in output
            assert "level3" not in output
            assert "deep.py" not in output

    def test_empty_directory(self):
        """Verify empty directories appear with / suffix and no children."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("", encoding="utf-8")
            gen = TreeGenerator(root, use_gitignore=False)
            output = gen.scan()
            assert "logs/" in output
            assert "src/" in output
            assert "main.py" in output

    def test_nonexistent_path(self):
        """Verify ValueError is raised for non-existent paths."""
        with pytest.raises(ValueError, match="does not exist"):
            TreeGenerator("/nonexistent/path/that/does/not/exist")

    def test_builtin_noise_filtering_without_gitignore(self):
        """Verify default noise patterns filter common dirs even without .gitignore."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # No .gitignore
            _create_tree(root, {
                "node_modules": {
                    "pkg.js": None,
                },
                "__pycache__": {
                    "mod.pyc": None,
                },
                "src": {
                    "main.py": None,
                },
            })
            gen = TreeGenerator(root, use_gitignore=True)
            output = gen.scan()
            assert "node_modules" not in output
            assert "__pycache__" not in output
            assert "src/" in output

    def test_symlink_to_directory_skipped(self):
        """Verify symlinks to directories are skipped to avoid cycles."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "real_dir").mkdir()
            (root / "real_dir" / "file.txt").write_text("hello", encoding="utf-8")
            # Create symlink
            link = root / "link_to_real"
            try:
                link.symlink_to(root / "real_dir", target_is_directory=True)
            except OSError:
                pytest.skip("Symlinks not supported on this platform")
            gen = TreeGenerator(root, use_gitignore=False)
            output = gen.scan()
            assert "link_to_real" not in output or "real_dir" in output
