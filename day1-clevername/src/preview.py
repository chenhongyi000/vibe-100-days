"""
预览面板模块
使用 rich 表格展示新旧文件名对照，高亮冲突项
"""

from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .rules import RenamePlan, Conflict

console = Console()

# 预览显示的最大行数
MAX_PREVIEW_ROWS = 8


def _format_size(bytes_count: int) -> str:
    """格式化文件大小为人类可读格式"""
    if bytes_count is None:
        return "N/A"
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} TB"


def show_preview(plans: list[RenamePlan], conflicts: list[Conflict] | None = None):
    """
    显示重命名预览表格

    Args:
        plans: 重命名计划列表
        conflicts: 冲突列表（可选）
    """
    if not plans:
        console.print("[yellow]没有文件需要重命名[/]")
        return

    table = Table(
        title="📋 重命名预览",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white",
        title_style="bold cyan",
        expand=True,
    )

    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("原文件名", style="red", max_width=40)
    table.add_column("→", style="dim", width=2)
    table.add_column("新文件名", style="green", max_width=40)
    table.add_column("大小", style="dim", width=8, justify="right")

    total = len(plans)
    show_count = min(total, MAX_PREVIEW_ROWS)

    # 冲突名称集合
    conflict_names = set()
    if conflicts:
        for c in conflicts:
            conflict_names.add(c.new_name.lower())

    # 显示前 N-2 条
    head_count = show_count - 2 if total > show_count else show_count
    for i, plan in enumerate(plans[:head_count]):
        _add_plan_row(table, i + 1, plan, conflict_names)

    # 省略号
    if total > show_count:
        table.add_row("...", "...", "", "...", "...")

    # 显示最后 2 条
    if total > show_count:
        for i, plan in enumerate(plans[-2:]):
            idx = total - 1 + i
            _add_plan_row(table, idx, plan, conflict_names)

    console.print()
    console.print(table)

    # 显示统计
    console.print(f"   共 {total} 个文件", style="dim")

    # 冲突警告
    if conflicts:
        console.print()
        console.print(f"⚠️  检测到 {len(conflicts)} 个文件名冲突：", style="bold red")
        for c in conflicts:
            files = ", ".join(p.name for p in c.paths)
            console.print(f"   • {c.new_name} ← {files}", style="red")


def _add_plan_row(table: Table, idx: int, plan: RenamePlan, conflict_names: set):
    """向表格添加一行，冲突项高亮"""
    try:
        size = plan.original.stat().st_size
    except Exception:
        size = 0

    original_text = Text(plan.original.name)
    new_text = Text(plan.new_name)

    # 冲突项红色高亮
    if plan.new_name.lower() in conflict_names:
        original_text.stylize("bold red")
        new_text.stylize("bold red")

    table.add_row(
        str(idx),
        original_text,
        "→",
        new_text,
        _format_size(size),
    )