#!/usr/bin/env python3
"""
CleverName (灵名) — 智能批量文件重命名工具
让杂乱无章的照片和文件，一秒拥有会说话的姓名

用法:
    python clevername.py
    python clevername.py /path/to/folder
"""

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).parent))

from src.scanner import scan_files, clean_path, classify_files, FILTER_PRESETS
from src.rules import RuleEngine, TEMPLATES
from src.preview import show_preview
from src.executor import execute_rename, generate_undo
from src.ai_labeler import is_ai_available, batch_label
from src.ui import (
    print_banner,
    print_step,
    success,
    warning,
    error,
    info,
    confirm,
    ask,
    console,
    print_summary,
)


def step1_import(args_path: str | None = None) -> list[Path]:
    """Step 1: 导入文件"""
    print_step(1, "导入文件")

    # 获取路径
    if args_path:
        path_str = args_path
    else:
        path_str = ask("📁 请将文件/文件夹拖入此处，或输入路径")
        path_str = clean_path(path_str)

    if not path_str:
        error("未输入路径，程序退出")
        sys.exit(0)

    folder = Path(path_str)
    if not folder.exists():
        error(f"路径不存在: {path_str}")
        sys.exit(1)

    # 如果是单个文件，直接返回
    if folder.is_file():
        console.print(f"   检测到单个文件: {folder.name}", style="dim")
        return [folder]

    # 选择文件类型过滤
    console.print()
    console.print("   📂 选择文件类型过滤：", style="cyan")
    for key, (name, _) in FILTER_PRESETS.items():
        console.print(f"   [{key}] {name}")
    console.print(f"   [直接回车] 全部文件")

    choice = ask("   请选择").strip()

    if choice in FILTER_PRESETS:
        name, extensions = FILTER_PRESETS[choice]
        console.print(f"   已选择: {name}", style="dim")
    else:
        name, extensions = "全部文件", None

    # 扫描文件
    files = scan_files(str(folder), extensions=extensions)
    image_count, video_count = classify_files(files)

    success(f"扫描完成：共找到 {len(files)} 个文件")
    print_summary(len(files), image_count, video_count)

    if not files:
        error("未找到符合条件的文件，程序退出")
        sys.exit(0)

    return files


def step2_config(files: list[Path]) -> tuple[str, int]:
    """Step 2: 配置命名规则"""
    print_step(2, "配置命名规则")

    # 显示模板选项
    console.print()
    console.print("   📐 请选择命名模板：", style="cyan")
    console.print()

    for key, tmpl in TEMPLATES.items():
        # 模板 3 如果 AI 不可用，标记为需要配置
        note = ""
        if key == "3" and not is_ai_available():
            note = " [dim](需配置 AI)[/dim]"
        console.print(f"   [{key}] {tmpl['name']}")
        console.print(f"       示例: {tmpl['example']}", style="dim")
        console.print(f"       说明: {tmpl['description']}{note}", style="dim")
        console.print()

    console.print("   [4] 自定义组合")
    console.print("       输入 token 组合，如: {date}_{original}_{counter}")
    console.print()

    choice = ask("   请输入编号").strip()

    # 获取模板
    if choice == "4":
        console.print()
        console.print("   📝 可用 token：", style="cyan")
        console.print("   {date}       — 拍摄/修改日期 (2024-01-15_143022)")
        console.print("   {counter}    — 自动补零计数器 (001, 002...)")
        console.print("   {original}   — 原始文件名（不含扩展名）")
        console.print("   {original:N} — 原始文件名前 N 个字符")
        console.print("   {ai_desc}    — AI 语义标签")
        console.print("   {ext}        — 原始扩展名 (.jpg)")
        console.print()
        template = ask("   请输入模板").strip()
        if not template:
            warning("未输入模板，使用默认模板 [1]")
            template = TEMPLATES["1"]["template"]
    elif choice in TEMPLATES:
        template = TEMPLATES[choice]["template"]
    else:
        warning(f"无效选择，使用默认模板 [1]")
        template = TEMPLATES["1"]["template"]

    console.print(f"   模板: {template}", style="green")

    # 计数器位数
    console.print()
    digits_str = ask("   计数器位数（默认 3）").strip()
    try:
        counter_digits = int(digits_str) if digits_str else 3
        counter_digits = max(1, min(counter_digits, 10))  # 限制 1-10
    except ValueError:
        counter_digits = 3

    console.print(f"   计数器位数: {counter_digits}", style="green")

    return template, counter_digits


def step3_preview_and_commit(
    files: list[Path],
    template: str,
    counter_digits: int,
):
    """Step 3: 预览并执行"""
    print_step(3, "预览确认")

    engine = RuleEngine(counter_digits=counter_digits)

    # AI 标签（如果模板需要）
    if "{ai_desc}" in template and is_ai_available():
        console.print()
        labels = batch_label(files)
        # 将标签注入到 engine 的 file_info 构建中 —— 这里我们通过
        # 自定义方式注入，因为 batch_label 是独立步骤
        # 简化处理：在生成 plan 前先获取标签，然后手动设置
        console.print()

    # 生成重命名计划
    plans = engine.generate_plan(files, template)

    # AI 标签补充（如果模板需要）
    if "{ai_desc}" in template and is_ai_available():
        labels = batch_label(files)
        if labels:
            # 重建计划，注入 AI 标签
            engine.reset_counter()
            # 重新生成计划时注入标签
            # 这里简化：直接修改 plans 中的文件名
            import re
            for plan in plans:
                fpath = plan.original
                if fpath in labels:
                    plan.new_name = re.sub(r"未识别", labels[fpath], plan.new_name)
            console.print()

    # 冲突检测
    conflicts = engine.detect_conflicts(plans)
    if conflicts:
        console.print()
        warning(f"检测到 {len(conflicts)} 个文件名冲突，已自动处理")
        plans = engine.resolve_conflicts(plans)

    # 显示预览
    show_preview(plans, conflicts)

    # 确认执行
    if not confirm("确认执行重命名？"):
        info("已取消操作")
        sys.exit(0)

    # 执行
    console.print()
    succeeded = execute_rename(plans)

    if succeeded:
        # 生成回滚脚本（放在目标文件夹中）
        if succeeded:
            # 所有文件在同一个文件夹
            output_dir = succeeded[0].new_path.parent
        else:
            output_dir = Path.cwd()

        # 回滚脚本需要反向映射（新名称 → 原名称）
        generate_undo(succeeded, output_dir)

    console.print()
    if succeeded:
        success("感谢使用 CleverName 灵名！")
    else:
        warning("部分文件重命名失败，请检查错误信息")


def main():
    """主入口"""
    print_banner()

    # 支持命令行参数
    args_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        # Step 1: 导入
        files = step1_import(args_path)

        # Step 2: 配置
        template, counter_digits = step2_config(files)

        # Step 3: 预览并执行
        step3_preview_and_commit(files, template, counter_digits)

    except KeyboardInterrupt:
        console.print()
        warning("操作已取消")
        sys.exit(0)
    except Exception as e:
        error(f"发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()