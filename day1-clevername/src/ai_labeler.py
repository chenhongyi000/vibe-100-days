"""
AI 语义标签模块（P1 可选功能）
支持 OpenAI 兼容接口和本地 Ollama 模型，无配置时优雅降级
"""

import base64
import os
from pathlib import Path
from typing import Optional

from .ui import console, warning, info, success

# 环境变量配置
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
AI_MODEL = os.environ.get("CLEVERNAME_AI_MODEL", "gpt-4o-mini")  # 默认用便宜的模型


def is_ai_available() -> bool:
    """检查 AI 功能是否可用"""
    if OPENAI_API_KEY:
        return True

    # 检查本地 Ollama
    try:
        import urllib.request

        req = urllib.request.Request("http://localhost:11434/api/tags")
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        return False


def get_ai_source() -> str:
    """返回当前 AI 来源"""
    if OPENAI_API_KEY:
        return f"云端 API ({AI_MODEL})"
    return "本地 Ollama"


def label_image(filepath: Path) -> str:
    """
    使用 AI 识别图片内容，生成中文语义标签

    Args:
        filepath: 图片文件路径

    Returns:
        中文标签，如 "金毛犬_草地"
    """
    if not is_ai_available():
        return ""

    if OPENAI_API_KEY:
        return _label_via_api(filepath)
    else:
        return _label_via_ollama(filepath)


def _label_via_api(filepath: Path) -> str:
    """通过 OpenAI 兼容 API 生成标签"""
    try:
        from openai import OpenAI

        # 读取图片并转为 base64
        with open(filepath, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = filepath.suffix.lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}
        mime_type = mime_map.get(ext, "image/jpeg")

        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "用2-3个中文词描述这张图片的主要内容，用下划线连接，不要超过15个字。例如：金毛犬_草地、城市夜景_车流、美食_蛋糕。只输出标签，不要其他内容。",
                        },
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                    ],
                }
            ],
            max_tokens=20,
            temperature=0.3,
        )

        label = response.choices[0].message.content.strip()
        # 清理多余字符
        label = label.replace(" ", "_").replace("，", "_").replace(",", "_")
        return label

    except ImportError:
        warning("openai 库未安装，跳过 AI 标签。安装: pip install openai")
        return ""
    except Exception as e:
        warning(f"AI 标签生成失败: {e}")
        return ""


def _label_via_ollama(filepath: Path) -> str:
    """通过本地 Ollama 生成标签"""
    try:
        import json
        import urllib.request

        # 读取图片并转为 base64
        with open(filepath, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        payload = json.dumps({
            "model": "llava",  # Ollama 的多模态模型
            "prompt": "用2-3个中文词描述这张图片的主要内容，用下划线连接，不要超过15个字。例如：金毛犬_草地、城市夜景_车流。只输出标签，不要其他内容。",
            "images": [image_data],
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        label = result.get("response", "").strip()
        label = label.replace(" ", "_").replace("，", "_").replace(",", "_")
        return label

    except Exception as e:
        warning(f"Ollama 标签生成失败: {e}")
        return ""


def batch_label(files: list[Path]) -> dict[Path, str]:
    """
    批量生成 AI 标签

    Args:
        files: 图片文件路径列表

    Returns:
        {文件路径: 标签} 字典
    """
    if not is_ai_available():
        info("AI 功能未配置，跳过语义标签")
        info("配置方式：设置 OPENAI_API_KEY 环境变量，或启动本地 Ollama")
        return {}

    source = get_ai_source()
    console.print(f"🤖 正在使用 {source} 识别图片内容...", style="cyan")

    # 只对图片文件生成标签
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
    image_files = [f for f in files if f.suffix.lower() in image_exts]

    if not image_files:
        return {}

    labels = {}
    for i, f in enumerate(image_files):
        console.print(f"   [{i + 1}/{len(image_files)}] {f.name}...", style="dim")
        label = label_image(f)
        if label:
            labels[f] = label
            console.print(f"   ✅ {f.name} → {label}", style="green")

    success(f"AI 标签生成完成：{len(labels)}/{len(image_files)} 个")
    return labels