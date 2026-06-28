"""Integration tests for wttr-cli CLI."""

import subprocess
import sys
import os
import pytest


SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
CLI_PATH = os.path.join(SRC_DIR, "wttr_cli.py")


def run_wttr(*args: str) -> subprocess.CompletedProcess:
    """Run wttr-cli with given arguments and return the result."""
    return subprocess.run(
        [sys.executable, CLI_PATH, *args],
        capture_output=True,
        encoding="utf-8",
        timeout=30,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


class TestCLIBasic:
    """Basic CLI tests that don't require network (use --help, --version)."""

    def test_help_flag(self):
        result = run_wttr("--help")
        assert result.returncode == 0
        assert "wttr" in result.stdout
        assert "终端天气极简仪" in result.stdout

    def test_version_flag(self):
        result = run_wttr("--version")
        assert result.returncode == 0
        assert "wttr-cli" in result.stdout
        assert "0.1.0" in result.stdout

    def test_invalid_days_rejected(self):
        """--days 0 should be rejected by argparse choices."""
        result = run_wttr("--days", "0")
        assert result.returncode != 0

    def test_invalid_days_too_high(self):
        """--days 5 should be rejected by argparse choices."""
        result = run_wttr("--days", "5")
        assert result.returncode != 0


@pytest.mark.network
class TestCLINetwork:
    """CLI tests that require network access to wttr.in."""

    def test_auto_detect_location(self):
        """wttr with no args should auto-detect and show weather."""
        result = run_wttr()
        assert result.returncode == 0
        # Should have some output
        assert len(result.stdout.strip()) > 0

    def test_simple_mode(self):
        """--simple should produce plain text output."""
        result = run_wttr("Beijing", "--simple")
        assert result.returncode == 0
        output = result.stdout.strip()
        assert "Beijing" in output
        assert "°C" in output
        assert "|" in output  # simple mode uses pipe separators

    def test_simple_mode_no_newlines(self):
        """--simple output should be a single line."""
        result = run_wttr("Beijing", "--simple")
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1

    def test_chinese_city_name(self):
        """Chinese city name should work."""
        result = run_wttr("北京")
        assert result.returncode == 0

    def test_english_city_name(self):
        """English city name should work."""
        result = run_wttr("Beijing")
        assert result.returncode == 0

    def test_city_with_spaces(self):
        """City names with spaces should be URL-encoded correctly."""
        result = run_wttr("New York")
        assert result.returncode == 0

    def test_forecast_days_1(self):
        """--days 1 should produce forecast table."""
        result = run_wttr("Beijing", "--days", "1")
        assert result.returncode == 0

    def test_nonexistent_city(self):
        """Non-existent city should fail gracefully."""
        result = run_wttr("XyzzyNoSuchCity12345")
        assert result.returncode != 0
        assert "未找到" in result.stderr or "未找到" in result.stdout