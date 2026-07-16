from __future__ import annotations

import argparse
from pathlib import Path

from src.wechat_article_pusher import (
    build_payload,
    load_config,
    parse_frontmatter,
    resolve_credentials,
    resolve_image_path,
    upload_and_rewrite_images,
    ArticleMeta,
)


class FakeClient:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    def upload_content_image(self, path: Path) -> str:
        self.paths.append(path)
        return f"https://img.example.com/{path.name}"


def test_parse_frontmatter_reads_basic_values() -> None:
    meta, body = parse_frontmatter(
        """---
title: "自动推送公众号文章"
summary: "省掉复制粘贴"
tags:
  - wechat
---
# 正文
"""
    )

    assert meta["title"] == "自动推送公众号文章"
    assert meta["summary"] == "省掉复制粘贴"
    assert meta["tags"] == ["wechat"]
    assert body == "# 正文"


def test_upload_and_rewrite_images_replaces_local_src(tmp_path: Path) -> None:
    image = tmp_path / "cover.png"
    image.write_bytes(b"fake")
    html = '<p>hi</p><img src="cover.png" alt="cover"><img src="https://example.com/a.png">'
    client = FakeClient()

    rewritten, uploaded = upload_and_rewrite_images(html, tmp_path, client)  # type: ignore[arg-type]

    assert 'src="https://img.example.com/cover.png"' in rewritten
    assert 'src="https://example.com/a.png"' in rewritten
    assert uploaded == {"cover.png": "https://img.example.com/cover.png"}
    assert client.paths == [image]


def test_resolve_image_path_ignores_remote_urls(tmp_path: Path) -> None:
    assert resolve_image_path("https://example.com/a.png", tmp_path) is None
    assert resolve_image_path("assets/a.png", tmp_path) == tmp_path / "assets" / "a.png"


def test_build_payload_matches_wechat_draft_shape() -> None:
    meta = ArticleMeta(
        title="标题",
        author="作者",
        digest="摘要",
        content_source_url="https://example.com",
        need_open_comment=1,
        only_fans_can_comment=0,
    )

    payload = build_payload(meta, "<p>正文</p>", "thumb123")

    assert payload["articles"][0]["title"] == "标题"
    assert payload["articles"][0]["thumb_media_id"] == "thumb123"
    assert payload["articles"][0]["content"] == "<p>正文</p>"


def test_load_config_reads_local_credentials(tmp_path: Path) -> None:
    config_path = tmp_path / "config.local.json"
    config_path.write_text('{"appid": "wx123", "appsecret": "secret123"}', encoding="utf-8")

    config = load_config(config_path)

    assert config["appid"] == "wx123"
    assert config["appsecret"] == "secret123"


def test_resolve_credentials_prefers_cli_over_config() -> None:
    args = argparse.Namespace(appid="cli-appid", secret="cli-secret")

    credentials = resolve_credentials(args, {"appid": "config-appid", "appsecret": "config-secret"})

    assert credentials is not None
    assert credentials.appid == "cli-appid"
    assert credentials.secret == "cli-secret"
