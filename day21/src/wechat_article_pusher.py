#!/usr/bin/env python3
"""Create WeChat Official Account drafts from local Markdown or HTML."""

from __future__ import annotations

import argparse
import importlib.util
import json
import mimetypes
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


API_BASE = "https://api.weixin.qq.com/cgi-bin"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.local.json"
IMG_PATTERN = re.compile(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)
MD_IMAGE_PATTERN = re.compile(r"!\[[^\]]*]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


@dataclass(frozen=True)
class ArticleMeta:
    title: str
    author: str
    digest: str
    content_source_url: str
    need_open_comment: int
    only_fans_can_comment: int


@dataclass(frozen=True)
class PushResult:
    draft_media_id: str | None
    publish_id: str | None
    image_count: int
    uploaded_images: dict[str, str]
    payload: dict[str, Any]


class WeChatApiError(RuntimeError):
    """Raised when the WeChat API returns an error response."""


@dataclass(frozen=True)
class WeChatCredentials:
    appid: str
    secret: str


class WeChatClient:
    def __init__(self, appid: str, secret: str, *, api_base: str = API_BASE) -> None:
        self.appid = appid
        self.secret = secret
        self.api_base = api_base.rstrip("/")
        self._access_token: str | None = None

    @property
    def access_token(self) -> str:
        if self._access_token is None:
            url = (
                f"{self.api_base}/token?"
                + urllib.parse.urlencode(
                    {"grant_type": "client_credential", "appid": self.appid, "secret": self.secret}
                )
            )
            data = self._request_json("GET", url)
            token = data.get("access_token")
            if not token:
                raise WeChatApiError(f"获取 access_token 失败: {data}")
            self._access_token = str(token)
        return self._access_token

    def upload_content_image(self, path: Path) -> str:
        url = self._url("/media/uploadimg")
        data = self._multipart_request(url, "media", path)
        image_url = data.get("url")
        if not image_url:
            raise WeChatApiError(f"上传正文图片失败: {data}")
        return str(image_url)

    def upload_thumb(self, path: Path) -> str:
        url = self._url("/material/add_material", {"type": "thumb"})
        data = self._multipart_request(url, "media", path)
        media_id = data.get("media_id")
        if not media_id:
            raise WeChatApiError(f"上传封面图失败: {data}")
        return str(media_id)

    def add_draft(self, payload: dict[str, Any]) -> str:
        data = self._post_json(self._url("/draft/add"), payload)
        media_id = data.get("media_id")
        if not media_id:
            raise WeChatApiError(f"创建草稿失败: {data}")
        return str(media_id)

    def publish(self, draft_media_id: str) -> str:
        data = self._post_json(self._url("/freepublish/submit"), {"media_id": draft_media_id})
        publish_id = data.get("publish_id")
        if not publish_id:
            raise WeChatApiError(f"提交发布失败: {data}")
        return str(publish_id)

    def _url(self, path: str, params: dict[str, str] | None = None) -> str:
        query = {"access_token": self.access_token}
        if params:
            query.update(params)
        return f"{self.api_base}{path}?{urllib.parse.urlencode(query)}"

    def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="POST")
        request.add_header("Content-Type", "application/json; charset=utf-8")
        return self._open_json(request)

    def _request_json(self, method: str, url: str) -> dict[str, Any]:
        return self._open_json(urllib.request.Request(url, method=method))

    def _multipart_request(self, url: str, field_name: str, path: Path) -> dict[str, Any]:
        boundary = "----vibe100wechatboundary"
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; filename="{path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8")
        footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
        body = header + path.read_bytes() + footer
        request = urllib.request.Request(url, data=body, method="POST")
        request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        request.add_header("Content-Length", str(len(body)))
        return self._open_json(request)

    def _open_json(self, request: urllib.request.Request) -> dict[str, Any]:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - user-supplied API call.
            data = json.loads(response.read().decode("utf-8"))
        if data.get("errcode") not in (None, 0):
            raise WeChatApiError(json.dumps(data, ensure_ascii=False))
        return data


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, normalized.strip()

    end_index = next((index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"), None)
    if end_index is None:
        return {}, normalized.strip()

    meta: dict[str, Any] = {}
    current_key: str | None = None
    for line in lines[1:end_index]:
        stripped = line.strip()
        if stripped.startswith("- ") and current_key:
            value = stripped[2:].strip().strip("\"'")
            existing = meta.setdefault(current_key, [])
            if isinstance(existing, list):
                existing.append(value)
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if not value:
            meta[key] = []
        else:
            meta[key] = value.strip("\"'")

    return meta, "\n".join(lines[end_index + 1 :]).strip()


def render_input(input_path: Path) -> tuple[dict[str, Any], str]:
    text = input_path.read_text(encoding="utf-8")
    if input_path.suffix.lower() in {".htm", ".html"}:
        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else input_path.stem
        body_match = re.search(r"<body[^>]*>(.*?)</body>", text, re.IGNORECASE | re.DOTALL)
        return {"title": title}, body_match.group(1).strip() if body_match else text

    meta, body = parse_frontmatter(text)
    renderer = load_day5_renderer()
    if renderer:
        return meta, renderer(body)
    return meta, fallback_markdown_to_html(body)


def load_day5_renderer() -> Any | None:
    renderer_path = Path(__file__).resolve().parents[2] / "day5" / "src" / "wechat_md.py"
    if not renderer_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("vibe100_day5_wechat_md", renderer_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, "render_markdown", None)


def fallback_markdown_to_html(text: str) -> str:
    blocks: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{escape_html(heading.group(2))}</h{level}>")
        elif stripped.startswith("!"):
            blocks.append(MD_IMAGE_PATTERN.sub(lambda m: f'<img src="{m.group(1)}">', stripped))
        else:
            blocks.append(f"<p>{escape_html(stripped)}</p>")
    return "\n".join(blocks)


def escape_html(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_config(config_path: Path | None) -> dict[str, Any]:
    if config_path is None or not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"配置文件 JSON 格式错误: {config_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"配置文件必须是 JSON 对象: {config_path}")
    return data


def resolve_credentials(args: argparse.Namespace, config: dict[str, Any]) -> WeChatCredentials | None:
    appid = args.appid or config.get("appid") or config.get("wechat_appid") or os.getenv("WECHAT_APPID")
    secret = (
        args.secret
        or config.get("appsecret")
        or config.get("secret")
        or config.get("wechat_appsecret")
        or os.getenv("WECHAT_APPSECRET")
    )
    if not appid or not secret:
        return None
    return WeChatCredentials(appid=str(appid), secret=str(secret))


def build_article_meta(args: argparse.Namespace, frontmatter: dict[str, Any], input_path: Path) -> ArticleMeta:
    title = args.title or frontmatter.get("title") or input_path.stem
    digest = args.digest or frontmatter.get("summary") or frontmatter.get("digest") or ""
    author = args.author or frontmatter.get("author") or ""
    source_url = args.source_url or frontmatter.get("source_url") or ""
    return ArticleMeta(
        title=str(title),
        author=str(author),
        digest=str(digest),
        content_source_url=str(source_url),
        need_open_comment=1 if args.open_comment else 0,
        only_fans_can_comment=1 if args.fans_comment_only else 0,
    )


def resolve_image_path(src: str, base_dir: Path) -> Path | None:
    parsed = urllib.parse.urlparse(src)
    if parsed.scheme in {"http", "https"} or src.startswith("//"):
        return None
    path = Path(urllib.parse.unquote(parsed.path))
    if not path.is_absolute():
        path = base_dir / path
    return path


def upload_and_rewrite_images(content: str, base_dir: Path, client: WeChatClient) -> tuple[str, dict[str, str]]:
    uploaded: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        src = match.group(1)
        local_path = resolve_image_path(src, base_dir)
        if local_path is None:
            return match.group(0)
        if not local_path.exists():
            raise FileNotFoundError(f"正文图片不存在: {local_path}")
        uploaded.setdefault(src, client.upload_content_image(local_path))
        return match.group(0).replace(src, uploaded[src])

    return IMG_PATTERN.sub(replace, content), uploaded


def build_payload(meta: ArticleMeta, content: str, thumb_media_id: str) -> dict[str, Any]:
    article = {
        "title": meta.title,
        "author": meta.author,
        "digest": meta.digest,
        "content": content,
        "content_source_url": meta.content_source_url,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": meta.need_open_comment,
        "only_fans_can_comment": meta.only_fans_can_comment,
    }
    return {"articles": [article]}


def push_article(
    input_path: Path,
    *,
    cover_path: Path,
    client: WeChatClient | None,
    args: argparse.Namespace,
) -> PushResult:
    frontmatter, content = render_input(input_path)
    meta = build_article_meta(args, frontmatter, input_path)

    if args.dry_run:
        rewritten, uploaded = content, {}
        thumb_media_id = args.thumb_media_id or "DRY_RUN_THUMB_MEDIA_ID"
        payload = build_payload(meta, rewritten, thumb_media_id)
        return PushResult(None, None, len(list(IMG_PATTERN.finditer(content))), uploaded, payload)

    if client is None:
        raise ValueError("非 dry-run 模式需要 WeChatClient")

    rewritten, uploaded = upload_and_rewrite_images(content, input_path.parent, client)
    thumb_media_id = args.thumb_media_id or client.upload_thumb(cover_path)
    payload = build_payload(meta, rewritten, thumb_media_id)
    draft_media_id = client.add_draft(payload)
    publish_id = client.publish(draft_media_id) if args.publish else None
    return PushResult(draft_media_id, publish_id, len(uploaded), uploaded, payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wechat-article-pusher",
        description="从本地 Markdown/HTML 创建微信公众号草稿，并可选择提交发布。",
    )
    parser.add_argument("input", help="文章 Markdown 或 HTML 文件")
    parser.add_argument("--cover", required=True, help="封面图路径；非 dry-run 时会上传为 thumb 素材")
    parser.add_argument(
        "--config",
        default=os.getenv("WECHAT_PUSHER_CONFIG") or str(DEFAULT_CONFIG_PATH),
        help="配置文件路径，默认读取 day21/config.local.json，也可用 WECHAT_PUSHER_CONFIG",
    )
    parser.add_argument("--appid", help="公众号 appid；优先级高于配置文件和 WECHAT_APPID")
    parser.add_argument("--secret", help="公众号 appsecret；优先级高于配置文件和 WECHAT_APPSECRET")
    parser.add_argument("--title", help="覆盖文章标题")
    parser.add_argument("--author", help="作者")
    parser.add_argument("--digest", help="摘要；默认读取 frontmatter summary/digest")
    parser.add_argument("--source-url", help="阅读原文链接")
    parser.add_argument("--thumb-media-id", help="复用已有封面 thumb_media_id，跳过封面上传")
    parser.add_argument("--open-comment", action="store_true", help="开启留言")
    parser.add_argument("--fans-comment-only", action="store_true", help="仅粉丝可留言")
    parser.add_argument("--publish", action="store_true", help="创建草稿后提交发布")
    parser.add_argument("--dry-run", action="store_true", help="只生成请求预览，不调用微信接口")
    parser.add_argument("--output-json", help="把结果写入 JSON 文件，便于检查或留档")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input)
    cover_path = Path(args.cover)
    config_path = Path(args.config) if args.config else None

    if not input_path.exists():
        print(f"错误: 文章文件不存在: {input_path}", file=sys.stderr)
        return 1
    if not args.dry_run and not args.thumb_media_id and not cover_path.exists():
        print(f"错误: 封面图不存在: {cover_path}", file=sys.stderr)
        return 1
    try:
        config = load_config(config_path)
    except ValueError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    credentials = resolve_credentials(args, config)
    if not args.dry_run and credentials is None:
        print(
            "错误: 请通过 --appid/--secret、day21/config.local.json，或 WECHAT_APPID/WECHAT_APPSECRET 配置公众号凭据。",
            file=sys.stderr,
        )
        return 1

    client = None if args.dry_run else WeChatClient(credentials.appid, credentials.secret)
    try:
        result = push_article(input_path, cover_path=cover_path, client=client, args=args)
    except (FileNotFoundError, ValueError, WeChatApiError, OSError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    output = asdict(result)
    if args.output_json:
        Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_json).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.dry_run:
        print("已生成 dry-run 草稿请求预览。")
    else:
        print(f"已创建公众号草稿: {result.draft_media_id}")
        if result.publish_id:
            print(f"已提交发布: {result.publish_id}")
    print(f"正文图片处理: {result.image_count} 张")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
