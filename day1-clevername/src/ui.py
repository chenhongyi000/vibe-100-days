"""
终端 UI 工具模块
提供统一的彩色输出、确认交互和界面装饰
"""

import sys

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_banner():
    """打印 CleverName 启动横幅"""
    banner = r"""
  ┌─────────────────────────────────────────┐
  │    🏷️  CleverName 灵名                  │
  │   让杂乱无章的照片和文件，              │
  │   一秒拥有会说话的姓名                  │
  └─────────────────────────────────────────┘
"""
    console.print(banner, style="bold cyan")


def print_step(step_num: int, title: str):
    """打印步骤标题"""
    console.print()
    console.print(f"━ Step {step_num}: {title} ", style="bold yellow")


def success(msg: str):
    """绿色成功信息"""
    console.print(f"✅ {msg}", style="bold green")


def warning(msg: str):
    """黄色警告信息"""
    console.print(f"⚠️  {msg}", style="bold yellow")


def error(msg: str):
    """红色错误信息"""
    console.print(f"❌ {msg}", style="bold red")


def info(msg: str):
    """蓝色提示信息"""
    console.print(f"💡 {msg}", style="blue")


def confirm(prompt: str) -> bool:
    """确认交互：返回 True/False"""
    console.print()
    result = console.input(f"[bold yellow]⚠️  {prompt} (y/n)[/] > ")
    return result.strip().lower() in ("y", "yes", "是")


def ask(prompt: str) -> str:
    """通用输入"""
    return console.input(f"[bold cyan]{prompt}[/] > ").strip()


def print_summary(file_count: int, image_count: int, video_count: int):
    """打印扫描结果摘要"""
    parts = [f"📷 图片: {image_count}", f"🎬 视频: {video_count}", f"📄 其他: {file_count - image_count - video_count}"]
    console.print(f"   {'  |  '.join(parts)}")