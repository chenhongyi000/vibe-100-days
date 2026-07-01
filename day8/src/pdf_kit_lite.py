#!/usr/bin/env python3
"""Small local PDF split/merge toolkit."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class PdfInfo:
    path: Path
    pages: int
    encrypted: bool


@dataclass(frozen=True)
class PageRange:
    start: int
    end: int

    def to_indexes(self, total_pages: int) -> range:
        start = self.start if self.start > 0 else total_pages + self.start + 1
        end = self.end if self.end > 0 else total_pages + self.end + 1
        if start < 1 or end < 1 or start > total_pages or end > total_pages or start > end:
            raise ValueError(f"页码范围无效: {self.start}-{self.end}，PDF 共 {total_pages} 页")
        return range(start - 1, end)


def read_pdf_info(path: Path) -> PdfInfo:
    reader = open_reader(path)
    return PdfInfo(path=path, pages=len(reader.pages), encrypted=reader.is_encrypted)


def merge_pdfs(inputs: list[Path], output: Path, overwrite: bool = False) -> int:
    if len(inputs) < 2:
        raise ValueError("合并至少需要 2 个 PDF 文件")
    ensure_output(output, overwrite)

    writer = PdfWriter()
    total_pages = 0
    for pdf_path in inputs:
        reader = open_reader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)
            total_pages += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as file:
        writer.write(file)
    return total_pages


def split_pdf(input_path: Path, output_dir: Path, ranges: list[PageRange] | None = None, prefix: str | None = None) -> list[Path]:
    reader = open_reader(input_path)
    total_pages = len(reader.pages)
    output_dir.mkdir(parents=True, exist_ok=True)
    name_prefix = prefix or input_path.stem

    if ranges:
        outputs = []
        for item in ranges:
            indexes = list(item.to_indexes(total_pages))
            output = output_dir / f"{name_prefix}_p{indexes[0] + 1}-{indexes[-1] + 1}.pdf"
            write_pages(reader, indexes, output)
            outputs.append(output)
        return outputs

    outputs = []
    for index in range(total_pages):
        output = output_dir / f"{name_prefix}_p{index + 1}.pdf"
        write_pages(reader, [index], output)
        outputs.append(output)
    return outputs


def write_pages(reader: PdfReader, indexes: list[int], output: Path) -> None:
    writer = PdfWriter()
    for index in indexes:
        writer.add_page(reader.pages[index])
    with output.open("wb") as file:
        writer.write(file)


def parse_ranges(text: str) -> list[PageRange]:
    ranges: list[PageRange] = []
    for raw_part in text.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part[1:]:
            start_text, end_text = part.split("-", 1)
            ranges.append(PageRange(parse_page_number(start_text), parse_page_number(end_text)))
        else:
            page = parse_page_number(part)
            ranges.append(PageRange(page, page))
    if not ranges:
        raise argparse.ArgumentTypeError("页码范围不能为空")
    return ranges


def parse_page_number(text: str) -> int:
    try:
        number = int(text.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"无效页码: {text}") from exc
    if number == 0:
        raise argparse.ArgumentTypeError("页码不能为 0")
    return number


def open_reader(path: Path) -> PdfReader:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"不是 PDF 文件: {path}")
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise ValueError(f"暂不支持加密 PDF: {path}")
    return reader


def ensure_output(output: Path, overwrite: bool) -> None:
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在，使用 --overwrite 覆盖: {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-kit-lite",
        description="本地 PDF 拆分、合并和页数查看工具。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    info = subparsers.add_parser("info", help="查看 PDF 页数")
    info.add_argument("files", nargs="+", help="PDF 文件")

    merge = subparsers.add_parser("merge", help="合并多个 PDF")
    merge.add_argument("files", nargs="+", help="待合并 PDF 文件，按传入顺序合并")
    merge.add_argument("-o", "--output", required=True, help="输出 PDF 文件")
    merge.add_argument("--overwrite", action="store_true", help="允许覆盖已存在输出文件")

    split = subparsers.add_parser("split", help="拆分 PDF")
    split.add_argument("file", help="待拆分 PDF 文件")
    split.add_argument("-o", "--output-dir", required=True, help="输出目录")
    split.add_argument("-r", "--ranges", type=parse_ranges, help="页码范围，例如 1-3,5,-1；不传则逐页拆分")
    split.add_argument("--prefix", help="输出文件名前缀，默认使用原文件名")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "info":
            for file in args.files:
                info = read_pdf_info(Path(file))
                print(f"{info.path}: {info.pages} 页")
            return 0

        if args.command == "merge":
            total_pages = merge_pdfs(
                [Path(file) for file in args.files],
                Path(args.output),
                overwrite=args.overwrite,
            )
            print(f"已合并 {len(args.files)} 个 PDF，共 {total_pages} 页 -> {args.output}")
            return 0

        if args.command == "split":
            outputs = split_pdf(
                Path(args.file),
                Path(args.output_dir),
                ranges=args.ranges,
                prefix=args.prefix,
            )
            print(f"已输出 {len(outputs)} 个 PDF 到 {args.output_dir}")
            for output in outputs:
                print(f"- {output}")
            return 0

    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    parser.error("未知命令")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
