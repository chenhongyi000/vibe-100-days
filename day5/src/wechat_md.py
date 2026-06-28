#!/usr/bin/env python3
"""Convert Markdown into WeChat-friendly inline HTML."""

from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


STYLES = {
    "article": (
        "max-width:680px;margin:0 auto;padding:8px 12px;"
        "color:#3f3f3f;font-size:16px;line-height:1.85;"
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',"
        "'Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif;"
    ),
    "h1": "margin:28px 0 18px;color:#121212;font-size:24px;line-height:1.35;font-weight:700;text-align:center;",
    "h2": "margin:26px 0 14px;padding-left:12px;border-left:4px solid #07c160;color:#1f1f1f;font-size:20px;line-height:1.45;font-weight:700;",
    "h3": "margin:22px 0 12px;color:#2b2b2b;font-size:18px;line-height:1.5;font-weight:700;",
    "h4": "margin:18px 0 10px;color:#444;font-size:16px;line-height:1.5;font-weight:700;",
    "p": "margin:0 0 14px;color:#3f3f3f;font-size:16px;line-height:1.85;text-align:justify;",
    "blockquote": "margin:14px 0;padding:12px 16px;background:#f7f8fa;border-left:4px solid #d0d7de;color:#57606a;font-size:15px;line-height:1.75;",
    "ul": "margin:8px 0 14px;padding-left:24px;color:#3f3f3f;font-size:16px;line-height:1.85;",
    "ol": "margin:8px 0 14px;padding-left:24px;color:#3f3f3f;font-size:16px;line-height:1.85;",
    "li": "margin:4px 0;",
    "pre": "margin:14px 0;padding:14px 16px;background:#24292f;border-radius:6px;overflow-x:auto;",
    "code_block": "color:#e6edf3;font-size:13px;line-height:1.65;font-family:Consolas,'SFMono-Regular','Liberation Mono',Menlo,monospace;white-space:pre;",
    "code": "padding:2px 6px;background:#f2f4f5;border-radius:4px;color:#d14;font-size:14px;font-family:Consolas,'SFMono-Regular','Liberation Mono',Menlo,monospace;",
    "hr": "margin:28px 0;border:0;border-top:1px solid #e5e7eb;",
    "table": "width:100%;margin:14px 0;border-collapse:collapse;color:#3f3f3f;font-size:14px;line-height:1.6;",
    "th": "padding:8px 10px;border:1px solid #d8dee4;background:#f6f8fa;color:#24292f;font-weight:700;text-align:left;",
    "td": "padding:8px 10px;border:1px solid #d8dee4;text-align:left;",
    "img": "max-width:100%;height:auto;margin:14px auto;border-radius:6px;display:block;",
    "a": "color:#576b95;text-decoration:none;",
}


@dataclass(frozen=True)
class ParsedMarkdown:
    metadata: dict[str, str]
    content: str


def parse_frontmatter(text: str) -> ParsedMarkdown:
    """Parse a simple YAML-like frontmatter block."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    if not lines or lines[0].strip() != "---":
        return ParsedMarkdown({}, normalized.strip())

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break

    if end_index is None:
        return ParsedMarkdown({}, normalized.strip())

    metadata: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            metadata[key] = value

    content = "\n".join(lines[end_index + 1 :]).strip()
    return ParsedMarkdown(metadata, content)


def render_markdown(text: str) -> str:
    """Render Markdown body into an inline-styled HTML fragment."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if not line.strip():
            index += 1
            continue

        if line.startswith("```"):
            html_block, index = _render_code_block(lines, index)
            blocks.append(html_block)
            continue

        if _is_table_start(lines, index):
            html_block, index = _render_table(lines, index)
            blocks.append(html_block)
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            text_html = format_inline(heading.group(2).strip())
            blocks.append(f'<h{level} style="{STYLES[f"h{level}"]}">{text_html}</h{level}>')
            index += 1
            continue

        if re.match(r"^\s*(---|\*\*\*|___)\s*$", line):
            blocks.append(f'<hr style="{STYLES["hr"]}">')
            index += 1
            continue

        if line.lstrip().startswith(">"):
            html_block, index = _render_blockquote(lines, index)
            blocks.append(html_block)
            continue

        if re.match(r"^\s*[-*+]\s+.+", line):
            html_block, index = _render_list(lines, index, ordered=False)
            blocks.append(html_block)
            continue

        if re.match(r"^\s*\d+[.)]\s+.+", line):
            html_block, index = _render_list(lines, index, ordered=True)
            blocks.append(html_block)
            continue

        html_block, index = _render_paragraph(lines, index)
        blocks.append(html_block)

    return "\n".join(blocks)


def format_inline(text: str) -> str:
    """Apply the inline Markdown subset used in articles."""
    code_spans: list[str] = []

    def keep_code(match: re.Match[str]) -> str:
        code = html.escape(match.group(1))
        code_spans.append(f'<code style="{STYLES["code"]}">{code}</code>')
        return f"@@CODE{len(code_spans) - 1}@@"

    escaped = re.sub(r"`([^`]+)`", keep_code, text)
    escaped = html.escape(escaped)

    escaped = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
        lambda m: (
            f'<img src="{html.escape(m.group(2), quote=True)}" '
            f'alt="{html.escape(m.group(1), quote=True)}" style="{STYLES["img"]}">'
        ),
        escaped,
    )
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
        lambda m: (
            f'<a href="{html.escape(m.group(2), quote=True)}" '
            f'style="{STYLES["a"]}">{m.group(1)}</a>'
        ),
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)

    for number, code_html in enumerate(code_spans):
        escaped = escaped.replace(f"@@CODE{number}@@", code_html)

    return escaped


def render_document(text: str, *, body_only: bool = False, title: str | None = None) -> str:
    """Render a Markdown document into full preview HTML or body-only HTML."""
    parsed = parse_frontmatter(text)
    document_title = title or parsed.metadata.get("title") or "Markdown 转公众号排版"
    body = render_markdown(parsed.content)
    article = f'<section style="{STYLES["article"]}">\n{body}\n</section>'

    if body_only:
        return article

    escaped_title = html.escape(document_title)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escaped_title}</title>
</head>
<body style="margin:0;background:#ffffff;">
{article}
</body>
</html>
"""


def convert_file(input_path: Path, output_path: Path | None, *, body_only: bool, title: str | None) -> str:
    if not input_path.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    text = input_path.read_text(encoding="utf-8")
    html_text = render_document(text, body_only=body_only, title=title)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_text, encoding="utf-8")

    return html_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wechat-md",
        description="Markdown 转微信公众号内联样式 HTML",
    )
    parser.add_argument("input", help="输入 Markdown 文件")
    parser.add_argument("-o", "--output", help="输出 HTML 文件；不提供则打印到终端")
    parser.add_argument("--body-only", action="store_true", help="只输出可复制到公众号编辑器的正文片段")
    parser.add_argument("--title", help="覆盖 HTML 预览页标题")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        html_text = convert_file(
            Path(args.input),
            Path(args.output) if args.output else None,
            body_only=args.body_only,
            title=args.title,
        )
    except FileNotFoundError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    if args.output:
        print(f"已输出: {args.output}")
    else:
        print(html_text)

    return 0


def _render_code_block(lines: list[str], index: int) -> tuple[str, int]:
    language = lines[index].strip().removeprefix("```").strip()
    index += 1
    code_lines: list[str] = []

    while index < len(lines) and not lines[index].startswith("```"):
        code_lines.append(lines[index])
        index += 1

    if index < len(lines):
        index += 1

    code = html.escape("\n".join(code_lines))
    language_label = f'<span style="color:#8b949e;font-size:12px;">{html.escape(language)}</span>\n' if language else ""
    block = (
        f'<pre style="{STYLES["pre"]}">'
        f'{language_label}<code style="{STYLES["code_block"]}">{code}</code>'
        "</pre>"
    )
    return block, index


def _render_blockquote(lines: list[str], index: int) -> tuple[str, int]:
    quote_lines: list[str] = []
    while index < len(lines) and lines[index].lstrip().startswith(">"):
        quote_lines.append(lines[index].lstrip()[1:].strip())
        index += 1
    content = "<br>".join(format_inline(line) for line in quote_lines if line)
    return f'<blockquote style="{STYLES["blockquote"]}">{content}</blockquote>', index


def _render_list(lines: list[str], index: int, *, ordered: bool) -> tuple[str, int]:
    pattern = r"^\s*\d+[.)]\s+(.+)" if ordered else r"^\s*[-*+]\s+(.+)"
    items: list[str] = []
    while index < len(lines):
        match = re.match(pattern, lines[index])
        if not match:
            break
        items.append(f'<li style="{STYLES["li"]}">{format_inline(match.group(1).strip())}</li>')
        index += 1
    tag = "ol" if ordered else "ul"
    return f'<{tag} style="{STYLES[tag]}">\n' + "\n".join(items) + f"\n</{tag}>", index


def _render_paragraph(lines: list[str], index: int) -> tuple[str, int]:
    paragraph_lines: list[str] = []
    while index < len(lines):
        line = lines[index]
        if not line.strip() or _starts_block(lines, index):
            break
        paragraph_lines.append(line.strip())
        index += 1

    content = "<br>".join(format_inline(line) for line in paragraph_lines)
    return f'<p style="{STYLES["p"]}">{content}</p>', index


def _is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    first = lines[index].strip()
    second = lines[index + 1].strip()
    if "|" not in first or "|" not in second:
        return False
    cells = _split_table_row(second)
    return bool(cells) and all(re.match(r"^:?-{3,}:?$", cell.strip()) for cell in cells)


def _render_table(lines: list[str], index: int) -> tuple[str, int]:
    header = _split_table_row(lines[index])
    index += 2
    rows: list[list[str]] = []

    while index < len(lines) and "|" in lines[index].strip():
        rows.append(_split_table_row(lines[index]))
        index += 1

    header_html = "".join(
        f'<th style="{STYLES["th"]}">{format_inline(cell.strip())}</th>' for cell in header
    )
    row_html = []
    for row in rows:
        cells = row + [""] * (len(header) - len(row))
        row_html.append(
            "<tr>"
            + "".join(f'<td style="{STYLES["td"]}">{format_inline(cell.strip())}</td>' for cell in cells[: len(header)])
            + "</tr>"
        )

    return (
        f'<table style="{STYLES["table"]}">\n'
        f"<thead><tr>{header_html}</tr></thead>\n"
        f"<tbody>\n" + "\n".join(row_html) + "\n</tbody>\n</table>",
        index,
    )


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _starts_block(lines: list[str], index: int) -> bool:
    line = lines[index]
    return (
        line.startswith("```")
        or _is_table_start(lines, index)
        or bool(re.match(r"^(#{1,4})\s+.+$", line))
        or bool(re.match(r"^\s*(---|\*\*\*|___)\s*$", line))
        or line.lstrip().startswith(">")
        or bool(re.match(r"^\s*[-*+]\s+.+", line))
        or bool(re.match(r"^\s*\d+[.)]\s+.+", line))
    )


if __name__ == "__main__":
    raise SystemExit(main())
