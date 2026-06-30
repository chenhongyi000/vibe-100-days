import json
from pathlib import Path

from src.dupe_scout import (
    ScanOptions,
    format_bytes,
    hash_file,
    parse_size,
    scan_duplicates,
    should_ignore,
)


def write_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_hash_file_same_content_same_digest(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    write_file(a, b"same content")
    write_file(b, b"same content")

    assert hash_file(a) == hash_file(b)


def test_scan_duplicates_groups_by_real_content(tmp_path: Path):
    write_file(tmp_path / "a.txt", b"same")
    write_file(tmp_path / "nested" / "b-copy.txt", b"same")
    write_file(tmp_path / "same-size-different.txt", b"diff")

    summary = scan_duplicates(ScanOptions(root=tmp_path))

    assert summary.scanned_files == 3
    assert len(summary.groups) == 1
    assert summary.groups[0].size == 4
    assert len(summary.groups[0].files) == 2
    assert summary.wasted_bytes == 4


def test_min_size_filters_small_duplicates(tmp_path: Path):
    write_file(tmp_path / "a.txt", b"same")
    write_file(tmp_path / "b.txt", b"same")

    summary = scan_duplicates(ScanOptions(root=tmp_path, min_size=5))

    assert len(summary.groups) == 0


def test_hidden_files_are_ignored_by_default(tmp_path: Path):
    write_file(tmp_path / ".hidden" / "a.txt", b"same")
    write_file(tmp_path / ".hidden" / "b.txt", b"same")

    summary = scan_duplicates(ScanOptions(root=tmp_path))

    assert summary.scanned_files == 0
    assert len(summary.groups) == 0


def test_include_hidden_scans_hidden_files(tmp_path: Path):
    write_file(tmp_path / ".hidden" / "a.txt", b"same")
    write_file(tmp_path / ".hidden" / "b.txt", b"same")

    summary = scan_duplicates(ScanOptions(root=tmp_path, include_hidden=True))

    assert len(summary.groups) == 1


def test_ignore_patterns_match_file_name_and_path():
    assert should_ignore(Path("notes/temp.tmp"), ("*.tmp",), include_hidden=True)
    assert should_ignore(Path("build/output.txt"), ("build",), include_hidden=True)
    assert not should_ignore(Path("notes/final.txt"), ("*.tmp",), include_hidden=True)


def test_json_and_csv_reports(tmp_path: Path):
    write_file(tmp_path / "a.txt", b"same")
    write_file(tmp_path / "b.txt", b"same")
    json_path = tmp_path / "reports" / "dupes.json"
    csv_path = tmp_path / "reports" / "dupes.csv"

    scan_duplicates(ScanOptions(root=tmp_path, json_path=json_path, csv_path=csv_path))

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["duplicate_groups"] == 1
    assert "a.txt" in csv_path.read_text(encoding="utf-8")


def test_parse_size_units():
    assert parse_size("1kb") == 1024
    assert parse_size("1.5mb") == 1572864
    assert parse_size("10") == 10


def test_format_bytes():
    assert format_bytes(10) == "10 B"
    assert format_bytes(2048) == "2.0 KB"
