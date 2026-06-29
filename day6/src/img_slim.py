#!/usr/bin/env python3
"""Batch image compressor for creator-friendly publishing workflows."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_OUTPUT_DIR = "compressed"


@dataclass(frozen=True)
class CompressOptions:
    input_path: Path
    output_dir: Path
    quality: int = 82
    max_width: int | None = 1600
    max_height: int | None = None
    recursive: bool = False
    keep_format: bool = True
    overwrite: bool = False
    dry_run: bool = False
    report_path: Path | None = None


@dataclass(frozen=True)
class CompressResult:
    source: Path
    output: Path
    original_bytes: int
    compressed_bytes: int
    original_size: tuple[int, int]
    output_size: tuple[int, int]
    status: str
    message: str = ""

    @property
    def saved_bytes(self) -> int:
        return self.original_bytes - self.compressed_bytes

    @property
    def saved_percent(self) -> float:
        if self.original_bytes <= 0:
            return 0.0
        return self.saved_bytes / self.original_bytes * 100


def find_images(input_path: Path, recursive: bool = False) -> list[Path]:
    """Find supported image files under a file or directory."""
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() in SUPPORTED_EXTENSIONS else []

    if not input_path.exists():
        raise FileNotFoundError(f"输入路径不存在: {input_path}")

    pattern = "**/*" if recursive else "*"
    return sorted(
        path
        for path in input_path.glob(pattern)
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def build_output_path(source: Path, options: CompressOptions) -> Path:
    """Build a stable output path while preserving relative folders."""
    input_is_file = options.input_path.suffix.lower() in SUPPORTED_EXTENSIONS
    if not input_is_file:
        try:
            relative = source.relative_to(options.input_path)
        except ValueError:
            relative = Path(source.name)
    else:
        relative = Path(source.name)

    if not options.keep_format:
        relative = relative.with_suffix(".jpg")

    return options.output_dir / relative


def calculate_target_size(width: int, height: int, max_width: int | None, max_height: int | None) -> tuple[int, int]:
    """Calculate resized dimensions without upscaling."""
    scale = 1.0
    if max_width and width > max_width:
        scale = min(scale, max_width / width)
    if max_height and height > max_height:
        scale = min(scale, max_height / height)

    if scale >= 1.0:
        return width, height

    return max(1, round(width * scale)), max(1, round(height * scale))


def compress_image(source: Path, options: CompressOptions) -> CompressResult:
    """Compress one image and return the result."""
    output = build_output_path(source, options)
    original_bytes = source.stat().st_size

    try:
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image)
            original_size = image.size
            target_size = calculate_target_size(
                image.width,
                image.height,
                options.max_width,
                options.max_height,
            )

            if options.dry_run:
                return CompressResult(
                    source=source,
                    output=output,
                    original_bytes=original_bytes,
                    compressed_bytes=original_bytes,
                    original_size=original_size,
                    output_size=target_size,
                    status="dry-run",
                )

            if output.exists() and not options.overwrite:
                return CompressResult(
                    source=source,
                    output=output,
                    original_bytes=original_bytes,
                    compressed_bytes=output.stat().st_size,
                    original_size=original_size,
                    output_size=target_size,
                    status="skipped",
                    message="output exists",
                )

            output.parent.mkdir(parents=True, exist_ok=True)

            if target_size != image.size:
                image = image.resize(target_size, Image.Resampling.LANCZOS)

            save_kwargs = _save_kwargs(output.suffix.lower(), options.quality)
            image_to_save = _prepare_image_for_format(image, output.suffix.lower())
            image_to_save.save(output, **save_kwargs)

    except UnidentifiedImageError:
        return CompressResult(
            source=source,
            output=output,
            original_bytes=original_bytes,
            compressed_bytes=0,
            original_size=(0, 0),
            output_size=(0, 0),
            status="failed",
            message="unidentified image",
        )

    return CompressResult(
        source=source,
        output=output,
        original_bytes=original_bytes,
        compressed_bytes=output.stat().st_size,
        original_size=original_size,
        output_size=target_size,
        status="compressed",
    )


def compress_batch(options: CompressOptions) -> list[CompressResult]:
    """Compress every supported image found in the input path."""
    images = find_images(options.input_path, options.recursive)
    results = [compress_image(path, options) for path in images]

    if options.report_path:
        write_report(results, options.report_path)

    return results


def write_report(results: list[CompressResult], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "source",
                "output",
                "status",
                "original_kb",
                "compressed_kb",
                "saved_percent",
                "original_size",
                "output_size",
                "message",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    str(result.source),
                    str(result.output),
                    result.status,
                    f"{result.original_bytes / 1024:.1f}",
                    f"{result.compressed_bytes / 1024:.1f}",
                    f"{result.saved_percent:.1f}",
                    f"{result.original_size[0]}x{result.original_size[1]}",
                    f"{result.output_size[0]}x{result.output_size[1]}",
                    result.message,
                ]
            )


def print_summary(results: list[CompressResult]) -> None:
    total_original = sum(item.original_bytes for item in results)
    total_output = sum(item.compressed_bytes for item in results)
    compressed = sum(1 for item in results if item.status == "compressed")
    skipped = sum(1 for item in results if item.status == "skipped")
    failed = sum(1 for item in results if item.status == "failed")
    dry_run = sum(1 for item in results if item.status == "dry-run")
    saved = total_original - total_output
    saved_percent = saved / total_original * 100 if total_original else 0

    print(f"扫描图片: {len(results)}")
    print(f"已压缩: {compressed}  跳过: {skipped}  失败: {failed}  预演: {dry_run}")
    print(f"原始大小: {_format_bytes(total_original)}")
    print(f"输出大小: {_format_bytes(total_output)}")
    print(f"节省空间: {_format_bytes(saved)} ({saved_percent:.1f}%)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="img-slim",
        description="批量压缩图片，适合公众号、博客和素材归档。",
    )
    parser.add_argument("input", help="输入图片文件或图片目录")
    parser.add_argument("-o", "--output-dir", default=DEFAULT_OUTPUT_DIR, help="输出目录，默认 compressed")
    parser.add_argument("-q", "--quality", type=int, default=82, help="JPEG/WebP 压缩质量，默认 82")
    parser.add_argument("--max-width", type=int, default=1600, help="最长宽度限制，默认 1600；传 0 表示不限制")
    parser.add_argument("--max-height", type=int, help="最大高度限制；默认不限制")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归扫描子目录")
    parser.add_argument("--to-jpg", action="store_true", help="统一输出为 JPG")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已存在输出文件")
    parser.add_argument("--dry-run", action="store_true", help="只预估处理结果，不写入文件")
    parser.add_argument("--report", help="输出 CSV 压缩报告")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not 1 <= args.quality <= 100:
        parser.error("--quality 必须在 1 到 100 之间")

    options = CompressOptions(
        input_path=Path(args.input),
        output_dir=Path(args.output_dir),
        quality=args.quality,
        max_width=args.max_width or None,
        max_height=args.max_height,
        recursive=args.recursive,
        keep_format=not args.to_jpg,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        report_path=Path(args.report) if args.report else None,
    )

    try:
        results = compress_batch(options)
    except FileNotFoundError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    print_summary(results)
    if options.report_path:
        print(f"报告: {options.report_path}")
    return 0 if all(item.status != "failed" for item in results) else 2


def _prepare_image_for_format(image: Image.Image, suffix: str) -> Image.Image:
    if suffix in {".jpg", ".jpeg"} and image.mode in {"RGBA", "LA", "P"}:
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.getchannel("A") if "A" in image.getbands() else None)
        return background
    return image


def _save_kwargs(suffix: str, quality: int) -> dict[str, object]:
    if suffix in {".jpg", ".jpeg"}:
        return {"format": "JPEG", "quality": quality, "optimize": True, "progressive": True}
    if suffix == ".webp":
        return {"format": "WEBP", "quality": quality, "method": 6}
    if suffix == ".png":
        return {"format": "PNG", "optimize": True, "compress_level": 9}
    return {}


def _format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1024 / 1024:.2f} MB"


if __name__ == "__main__":
    raise SystemExit(main())
