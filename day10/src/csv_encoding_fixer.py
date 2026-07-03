#!/usr/bin/env python3
"""Detect and convert CSV encodings safely."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from charset_normalizer import from_bytes
except Exception:  # pragma: no cover
    from_bytes = None

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


COMMON_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5", "cp1252", "latin1")


@dataclass(frozen=True)
class CsvFixResult:
    input: str
    output: str
    source_encoding: str
    target_encoding: str
    rows: int
    columns: int
    delimiter: str
    had_bom: bool
    replaced_errors: bool


def detect_encoding(data: bytes) -> str:
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"

    for encoding in COMMON_ENCODINGS:
        try:
            data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue

    if from_bytes is not None:
        match = from_bytes(data).best()
        if match and match.encoding:
            return match.encoding

    return "latin1"


def decode_csv(data: bytes, encoding: str) -> tuple[str, bool]:
    try:
        return data.decode(encoding), False
    except UnicodeDecodeError:
        return data.decode(encoding, errors="replace"), True


def sniff_dialect(text: str) -> csv.Dialect:
    sample = text[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        return csv.get_dialect("excel")


def count_csv_shape(text: str, dialect: csv.Dialect) -> tuple[int, int]:
    rows = list(csv.reader(text.splitlines(), dialect))
    if not rows:
        return 0, 0
    return len(rows), max(len(row) for row in rows)


def fix_csv_encoding(
    input_path: Path,
    output_path: Path,
    *,
    source_encoding: str | None = None,
    target_encoding: str = "utf-8-sig",
    overwrite: bool = False,
    report_path: Path | None = None,
) -> CsvFixResult:
    if not input_path.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在，使用 --overwrite 覆盖: {output_path}")

    data = input_path.read_bytes()
    detected = source_encoding or detect_encoding(data)
    text, replaced = decode_csv(data, detected)
    dialect = sniff_dialect(text)
    rows, columns = count_csv_shape(text, dialect)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding=target_encoding, newline="")

    result = CsvFixResult(
        input=str(input_path),
        output=str(output_path),
        source_encoding=detected,
        target_encoding=target_encoding,
        rows=rows,
        columns=columns,
        delimiter=getattr(dialect, "delimiter", ","),
        had_bom=data.startswith(b"\xef\xbb\xbf"),
        replaced_errors=replaced,
    )

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")

    return result


def print_result(result: CsvFixResult) -> None:
    print(f"输入: {result.input}")
    print(f"输出: {result.output}")
    print(f"源编码: {result.source_encoding}")
    print(f"目标编码: {result.target_encoding}")
    print(f"行数: {result.rows}")
    print(f"列数: {result.columns}")
    print(f"分隔符: {repr(result.delimiter)}")
    print(f"替换错误字符: {'是' if result.replaced_errors else '否'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="csv-encoding-fixer",
        description="检测并修复 CSV 编码，适合把 GBK/ANSI 等文件转换成 UTF-8。",
    )
    parser.add_argument("input", help="输入 CSV 文件")
    parser.add_argument("-o", "--output", required=True, help="输出 CSV 文件")
    parser.add_argument("--from-encoding", help="手动指定源编码，例如 gbk")
    parser.add_argument("--to-encoding", default="utf-8-sig", help="目标编码，默认 utf-8-sig，方便 Excel 打开")
    parser.add_argument("--report", help="输出 JSON 转换报告")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖输出文件")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = fix_csv_encoding(
            Path(args.input),
            Path(args.output),
            source_encoding=args.from_encoding,
            target_encoding=args.to_encoding,
            overwrite=args.overwrite,
            report_path=Path(args.report) if args.report else None,
        )
    except (FileNotFoundError, FileExistsError, LookupError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    print_result(result)
    if args.report:
        print(f"报告: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
