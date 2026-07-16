# wechat-article-pusher

WeChat Official Account article pusher for Day 21 of the Vibe Coding 100 days challenge.

It reads a local Markdown or HTML article, uploads local images, creates a WeChat Official Account draft, and can optionally submit the draft for publishing.

## Features

- Reads Markdown with frontmatter or an existing HTML file.
- Reuses the Day 5 Markdown renderer when this repository is available.
- Uploads local inline images and rewrites `<img src>` to WeChat image URLs.
- Uploads a cover image as `thumb_media_id`, or reuses an existing `--thumb-media-id`.
- Creates a draft through the WeChat draft API.
- Requires explicit `--publish` before submitting the draft for publishing.
- Provides `--dry-run` to inspect the generated payload without calling WeChat.
- Uses only the Python standard library.

## Install

No third-party dependency is required.

```powershell
python -m pip install -e .
```

## WeChat Setup

You need an enabled WeChat Official Account developer credential:

- `WECHAT_APPID`
- `WECHAT_APPSECRET`

The account also needs API permission for material upload, draft creation, and publishing.

You can configure credentials in any of these ways. CLI options have the highest priority, then the config file, then environment variables.

### Option 1: Local Config File

Copy `config.example.json` to `config.local.json`, then fill in your real values:

```json
{
  "appid": "your-wechat-appid",
  "appsecret": "your-wechat-appsecret"
}
```

The default config path is:

```text
day21/config.local.json
```

You can also use another path:

```powershell
python src\wechat_article_pusher.py article.md --cover assets\cover.png --config C:\secure\wechat-pusher.json
```

### Option 2: Environment Variables

```powershell
$env:WECHAT_APPID="your-appid"
$env:WECHAT_APPSECRET="your-secret"
python src\wechat_article_pusher.py article.md --cover assets\cover.png
```

### Option 3: CLI Options

```powershell
python src\wechat_article_pusher.py article.md --cover assets\cover.png --appid "your-appid" --secret "your-secret"
```

## Usage

Preview the payload without calling WeChat:

```powershell
python src\wechat_article_pusher.py examples\sample-article.md --cover assets\cover.png --dry-run --output-json examples\dry-run.json
```

Create a draft:

```powershell
python src\wechat_article_pusher.py article.md --cover assets\cover.png --author "Vibe Coding"
```

Create a draft and submit it for publishing:

```powershell
python src\wechat_article_pusher.py article.md --cover assets\cover.png --publish
```

Reuse an uploaded cover material:

```powershell
python src\wechat_article_pusher.py article.md --cover assets\cover.png --thumb-media-id "MEDIA_ID"
```

## Frontmatter

```yaml
---
title: "文章标题"
author: "作者"
summary: "文章摘要"
source_url: "https://github.com/chenhongyi000/vibe-100-days"
---
```

CLI options such as `--title`, `--author`, and `--digest` override frontmatter.

## Safety Notes

The tool defaults to creating a draft only. Add `--publish` only after the generated draft workflow is stable for your account.

Use `--dry-run --output-json` first when connecting a new account, because WeChat API permissions and IP whitelist settings vary by account.

## Test

```powershell
python -m pytest tests
```

## Project Structure

```text
day21/
  src/
    wechat_article_pusher.py
  tests/
    test_wechat_article_pusher.py
  examples/
    sample-article.md
  assets/
  README.md
  config.example.json
  requirements.txt
  pyproject.toml
```
