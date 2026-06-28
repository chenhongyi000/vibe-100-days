"""
执行器模块
负责批量重命名执行、进度条、回滚脚本生成
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .rules import RenamePlan
from .ui import console, success, warning, error, info


def execute_rename(plans: list[RenamePlan]) -> list[RenamePlan]:
    """
    执行批量重命名

    Args:
        plans: 重命名计划列表

    Returns:
        成功执行的重命名计划列表（用于生成回滚脚本）
    """
    if not plans:
        warning("没有需要重命名的文件")
        return []

    succeeded = []
    failed = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]重命名中...", total=len(plans))

        for plan in plans:
            try:
                # 检查目标文件是否已存在
                if plan.new_path.exists() and plan.new_path != plan.original:
                    raise FileExistsError(f"目标文件已存在: {plan.new_name}")

                # 执行重命名
                plan.original.rename(plan.new_path)
                succeeded.append(plan)
                progress.advance(task)

            except Exception as e:
                failed.append((plan, str(e)))
                progress.advance(task)

    # 结果汇总
    console.print()
    if succeeded:
        success(f"成功重命名 {len(succeeded)} 个文件")
    if failed:
        error(f"失败 {len(failed)} 个文件：")
        for plan, reason in failed:
            console.print(f"   • {plan.original.name} → {plan.new_name}: {reason}", style="red")

    return succeeded


def generate_undo(plans: list[RenamePlan], output_dir: Path):
    """
    生成回滚脚本和映射文件

    Args:
        plans: 成功执行的重命名计划
        output_dir: 输出目录（通常是原文件夹）
    """
    if not plans:
        return

    # 写入 JSON 映射文件
    mapping = {
        "created_at": datetime.now().isoformat(),
        "tool": "CleverName 灵名",
        "mappings": [
            {
                "original": str(plan.original.name),
                "renamed": plan.new_name,
                "original_path": str(plan.original),
                "new_path": str(plan.new_path),
            }
            for plan in plans
        ],
    }

    mapping_path = output_dir / "rename_mapping.json"
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    # 生成 restore.py 回滚脚本
    restore_py = _generate_restore_py(plans)
    restore_py_path = output_dir / "restore.py"
    restore_py_path.write_text(restore_py, encoding="utf-8")

    # 生成 restore.bat 双击回滚脚本
    restore_bat = _generate_restore_bat(restore_py_path)
    restore_bat_path = output_dir / "restore.bat"
    restore_bat_path.write_text(restore_bat, encoding="utf-8")

    info(f"回滚映射已保存: {mapping_path.name}")
    info(f"回滚脚本已保存: {restore_py_path.name}")
    info(f"双击可恢复: {restore_bat_path.name}")


def _generate_restore_py(plans: list[RenamePlan]) -> str:
    """生成 restore.py 脚本内容"""
    mappings_repr = []
    for plan in plans:
        new_name = plan.new_name
        original_name = plan.original.name
        mappings_repr.append(f'    ("{new_name}", "{original_name}"),')

    return f'''"""
CleverName 回滚脚本
运行此脚本可将文件恢复为原始名称
"""

import os
from pathlib import Path

# 重命名映射：(当前名称, 原始名称)
MAPPINGS = [
{chr(10).join(mappings_repr)}
]

def restore():
    """恢复原始文件名"""
    folder = Path(__file__).parent
    success = 0
    failed = 0

    for current_name, original_name in MAPPINGS:
        current_path = folder / current_name
        original_path = folder / original_name

        if not current_path.exists():
            print(f"⚠️  跳过（不存在）: {{current_name}}")
            failed += 1
            continue

        if original_path.exists():
            print(f"⚠️  跳过（原始文件已存在）: {{original_name}}")
            failed += 1
            continue

        try:
            current_path.rename(original_path)
            print(f"✅ {{current_name}} → {{original_name}}")
            success += 1
        except Exception as e:
            print(f"❌ {{current_name}}: {{e}}")
            failed += 1

    print(f"\\n完成！成功: {{success}}, 失败: {{failed}}")

if __name__ == "__main__":
    print("🔄 CleverName 回滚工具")
    print(f"共 {{len(MAPPINGS)}} 个文件待恢复\\n")
    confirm = input("确认恢复原始文件名？(y/n) > ")
    if confirm.strip().lower() in ("y", "yes", "是"):
        restore()
    else:
        print("已取消")
'''


def _generate_restore_bat(restore_py_path: Path) -> str:
    """生成 restore.bat 内容"""
    return f'''@echo off
chcp 65001 >nul
echo 🔄 CleverName 回滚工具
echo.
python "{restore_py_path.name}"
pause
'''