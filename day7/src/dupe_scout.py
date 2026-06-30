#!/usr/bin/env python3
"""Find duplicate files safely by size and SHA-256 hash."""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_IGNORES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
}


@dataclass(frozen=True)
class ScanOptions:
    root: Path
    min_size: int = 1
    include_hidden: bool = False
    ignore_patterns: tuple[str, ...] = ()
    json_path: Path | None = None
    csv_path: Path | None = None
    limit: int | None = None


@dataclass(frozen=True)
class FileInfo:
    path: Path
    size: int
    digest: str


@dataclass(frozen=True)
class DuplicateGroup:
    digest: str
    size: int
    files: tuple[Path, ...]

    @property
    def wasted_bytes(self) -> int:
        return self.size * (len(self.files) - 1)


@dataclass(frozen=True)
class ScanSummary:
    scanned_files: int
    candidate_files: int
    groups: tuple[DuplicateGroup, ...]

    @property
    def duplicate_files(self) -> int:
        return sum(len(group.files) for group in self.groups)

    @property
    def wasted_bytes(self) -> int:
        return sum(group.wasted_bytes for group in self.groups)


def scan_duplicates(options: ScanOptions) -> ScanSummary:
    if not options.root.exists():
        raise FileNotFoundError(f"路径不存在: {options.root}")
    if not options.root.is_dir():
        raise NotADirectoryError(f"不是文件夹: {options.root}")

    files = list(iter_files(options.root, options))
    size_groups: dict[int, list[Path]] = {}
    for path in files:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size >= options.min_size:
            size_groups.setdefault(size, []).append(path)

    candidates = [path for group in size_groups.values() if len(group) > 1 for path in group]
    digest_groups: dict[tuple[int, str], list[Path]] = {}

    for path in candidates:
        try:
            size = path.stat().st_size
            digest = hash_file(path)
        except OSError:
            continue
        digest_groups.setdefault((size, digest), []).append(path)

    groups = [
        DuplicateGroup(digest=digest, size=size, files=tuple(sorted(paths)))
        for (size, digest), paths in digest_groups.items()
        if len(paths) > 1
    ]
    groups.sort(key=lambda item: item.wasted_bytes, reverse=True)

    if options.limit:
        groups = groups[: options.limit]

    summary = ScanSummary(
        scanned_files=len(files),
        candidate_files=len(candidates),
        groups=tuple(groups),
    )

    if options.json_path:
        write_json(summary, options.json_path, options.root)
    if options.csv_path:
        write_csv(summary, options.csv_path, options.root)

    return summary


def iter_files(root: Path, options: ScanOptions):
    ignore_patterns = tuple(DEFAULT_IGNORES) + options.ignore_patterns
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if should_ignore(relative, ignore_patterns, options.include_hidden):
            continue
        yield path


def should_ignore(relative: Path, patterns: tuple[str, ...], include_hidden: bool = False) -> bool:
    parts = relative.parts
    if not include_hidden and any(part.startswith(".") for part in parts):
        return True
    text = relative.as_posix()
    for pattern in patterns:
        if pattern in parts or fnmatch.fnmatch(text, pattern) or fnmatch.fnmatch(relative.name, pattern):
            return True
    return False


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_json(summary: ScanSummary, output: Path, root: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scanned_files": summary.scanned_files,
        "candidate_files": summary.candidate_files,
        "duplicate_groups": len(summary.groups),
        "duplicate_files": summary.duplicate_files,
        "wasted_bytes": summary.wasted_bytes,
        "wasted_human": format_bytes(summary.wasted_bytes),
        "groups": [
            {
                "sha256": group.digest,
                "size": group.size,
                "size_human": format_bytes(group.size),
                "wasted_bytes": group.wasted_bytes,
                "wasted_human": format_bytes(group.wasted_bytes),
                "files": [path.relative_to(root).as_posix() for path in group.files],
            }
            for group in summary.groups
        ],
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(summary: ScanSummary, output: Path, root: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["group", "sha256", "size", "size_human", "wasted_bytes", "path"])
        for group_index, group in enumerate(summary.groups, start=1):
            for path in group.files:
                writer.writerow(
                    [
                        group_index,
                        group.digest,
                        group.size,
                        format_bytes(group.size),
                        group.wasted_bytes,
                        path.relative_to(root).as_posix(),
                    ]
                )


def print_summary(summary: ScanSummary, root: Path) -> None:
    print(f"扫描目录: {root}")
    print(f"扫描文件: {summary.scanned_files}")
    print(f"候选文件: {summary.candidate_files}")
    print(f"重复组数: {len(summary.groups)}")
    print(f"重复文件: {summary.duplicate_files}")
    print(f"可释放空间: {format_bytes(summary.wasted_bytes)}")

    if not summary.groups:
        print("没有发现重复文件。")
        return

    print()
    for index, group in enumerate(summary.groups, start=1):
        print(f"[{index}] {len(group.files)} 个文件 | 单个 {format_bytes(group.size)} | 可释放 {format_bytes(group.wasted_bytes)}")
        for file_path in group.files:
            print(f"    - {file_path.relative_to(root)}")


def parse_size(value: str) -> int:
    text = value.strip().lower()
    multiplier = 1
    if text.endswith("kb"):
        multiplier = 1024
        text = text[:-2]
    elif text.endswith("mb"):
        multiplier = 1024 * 1024
        text = text[:-2]
    elif text.endswith("gb"):
        multiplier = 1024 * 1024 * 1024
        text = text[:-2]
    elif text.endswith("b"):
        text = text[:-1]
    try:
        number = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"无效大小: {value}") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("--min-size 不能小于 0")
    return int(number * multiplier)


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / 1024 / 1024:.2f} MB"
    return f"{size / 1024 / 1024 / 1024:.2f} GB"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dupe-scout",
        description="安全扫描文件夹里的重复文件，按 SHA-256 确认重复内容。",
    )
    parser.add_argument("root", help="要扫描的文件夹")
    parser.add_argument("--min-size", type=parse_size, default=1, help="最小扫描大小，例如 1kb、10mb，默认 1B")
    parser.add_argument("--include-hidden", action="store_true", help="包含隐藏文件和隐藏目录")
    parser.add_argument("--ignore", action="append", default=[], help="额外忽略规则，可重复传入，例如 --ignore *.tmp")
    parser.add_argument("--json", dest="json_path", help="输出 JSON 报告")
    parser.add_argument("--csv", dest="csv_path", help="输出 CSV 报告")
    parser.add_argument("--limit", type=int, help="只展示空间浪费最多的前 N 组")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    options = ScanOptions(
        root=Path(args.root),
        min_size=args.min_size,
        include_hidden=args.include_hidden,
        ignore_patterns=tuple(args.ignore),
        json_path=Path(args.json_path) if args.json_path else None,
        csv_path=Path(args.csv_path) if args.csv_path else None,
        limit=args.limit,
    )

    try:
        summary = scan_duplicates(options)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    print_summary(summary, options.root)
    if options.json_path:
        print(f"JSON 报告: {options.json_path}")
    if options.csv_path:
        print(f"CSV 报告: {options.csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
