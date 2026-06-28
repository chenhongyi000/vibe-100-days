"""Integration tests for CLI interface."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PYTHON = sys.executable
CLI = str(Path(__file__).resolve().parent.parent / "src" / "tree_gen.py")


def run_cli(*args, cwd=None):
    """Run tree-gen CLI and return (returncode, stdout, stderr)."""
    cmd = [PYTHON, CLI] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
    )
    return result.returncode, result.stdout, result.stderr


class TestCLI:
    """CLI integration tests."""

    @pytest.fixture
    def sample_dir(self):
        """Create a temporary directory with sample files."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
            (root / "README.md").write_text("# Project", encoding="utf-8")
            yield root

    def test_stdout_output(self, sample_dir):
        """Verify output is printed to stdout."""
        rc, stdout, stderr = run_cli(str(sample_dir))
        assert rc == 0
        assert "src/" in stdout
        assert "main.py" in stdout

    def test_file_output(self, sample_dir):
        """Verify --output saves tree to a file."""
        out_file = str(sample_dir / "tree.md")
        rc, stdout, stderr = run_cli(str(sample_dir), "--output", out_file)
        assert rc == 0
        assert os.path.exists(out_file)
        content = Path(out_file).read_text(encoding="utf-8")
        assert "src/" in content
        assert "main.py" in content

    def test_overwrite_protection(self, sample_dir):
        """Verify existing output file is not overwritten by default."""
        out_file = str(sample_dir / "existing.md")
        Path(out_file).write_text("do not overwrite me", encoding="utf-8")
        rc, stdout, stderr = run_cli(str(sample_dir), "--output", out_file)
        assert rc == 1
        assert "Error" in stderr or "already exists" in stderr
        content = Path(out_file).read_text(encoding="utf-8")
        assert content == "do not overwrite me"

    def test_force_overwrite(self, sample_dir):
        """Verify --force allows overwriting existing output file."""
        out_file = str(sample_dir / "existing.md")
        Path(out_file).write_text("overwrite me", encoding="utf-8")
        rc, stdout, stderr = run_cli(str(sample_dir), "--output", out_file, "--force")
        assert rc == 0
        content = Path(out_file).read_text(encoding="utf-8")
        assert "src/" in content

    def test_no_gitignore_flag(self, sample_dir):
        """Verify --no-gitignore includes normally ignored files."""
        (sample_dir / ".gitignore").write_text("build/\n", encoding="utf-8")
        (sample_dir / "build").mkdir()
        (sample_dir / "build" / "output.js").write_text("/* bundled */", encoding="utf-8")
        # Without --no-gitignore: build/ should be excluded
        rc1, stdout1, _ = run_cli(str(sample_dir))
        assert "build" not in stdout1
        # With --no-gitignore: build/ should appear
        rc2, stdout2, _ = run_cli(str(sample_dir), "--no-gitignore")
        assert rc2 == 0
        assert "build/" in stdout2
        assert "output.js" in stdout2

    def test_version_flag(self):
        """Verify --version prints version string."""
        rc, stdout, stderr = run_cli("--version")
        assert rc == 0
        assert "tree-gen" in stdout

    def test_invalid_path(self):
        """Verify non-existent path gives error and exit code 1."""
        rc, stdout, stderr = run_cli("/nonexistent/path/that/does/not/exist")
        assert rc == 1
        assert "Error" in stderr or "does not exist" in stderr

    def test_depth_flag(self, sample_dir):
        """Verify --depth limits recursion."""
        (sample_dir / "deep").mkdir()
        (sample_dir / "deep" / "level2").mkdir()
        (sample_dir / "deep" / "level2" / "file.txt").write_text("", encoding="utf-8")
        rc, stdout, _ = run_cli(str(sample_dir), "--depth", "1")
        assert rc == 0
        assert "deep/" in stdout
        assert "level2" not in stdout
        assert "..." in stdout
