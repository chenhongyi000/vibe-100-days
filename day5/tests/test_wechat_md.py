from pathlib import Path

from src.wechat_md import format_inline, parse_frontmatter, render_document, render_markdown


def test_parse_frontmatter_returns_metadata_and_content():
    parsed = parse_frontmatter(
        """---
title: "Day 5"
series: vibe-100-days
---
# Hello
"""
    )

    assert parsed.metadata["title"] == "Day 5"
    assert parsed.metadata["series"] == "vibe-100-days"
    assert parsed.content == "# Hello"


def test_render_headings_paragraph_and_inline_styles():
    html = render_markdown("# 标题\n\n这是 **重点** 和 `code`。")

    assert '<h1 style="' in html
    assert "标题" in html
    assert "<strong>重点</strong>" in html
    assert '<code style="' in html
    assert "这是" in html


def test_render_code_block_escapes_html():
    html = render_markdown("```python\nprint('<hi>')\n```")

    assert '<pre style="' in html
    assert "python" in html
    assert "&lt;hi&gt;" in html
    assert "<hi>" not in html


def test_render_table():
    html = render_markdown("| 项目 | 状态 |\n| --- | --- |\n| Day5 | 待启动 |")

    assert '<table style="' in html
    assert "<thead><tr>" in html
    assert "Day5" in html
    assert "待启动" in html


def test_render_body_only_omits_document_shell():
    html = render_document("# 标题", body_only=True)

    assert html.startswith("<section")
    assert "<!DOCTYPE html>" not in html


def test_format_inline_renders_links_and_images():
    html = format_inline("看 [链接](https://example.com) 和 ![图](cover.png)")

    assert '<a href="https://example.com"' in html
    assert '<img src="cover.png"' in html


def test_cli_output_file(tmp_path: Path):
    from src.wechat_md import main

    source = tmp_path / "article.md"
    output = tmp_path / "article.html"
    source.write_text("# 标题\n\n正文", encoding="utf-8")

    assert main([str(source), "-o", str(output)]) == 0
    assert output.exists()
    assert "正文" in output.read_text(encoding="utf-8")
