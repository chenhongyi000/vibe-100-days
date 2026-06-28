"""
文件扫描器模块
负责递归遍历文件夹、按类型过滤文件、清理拖拽路径
"""

import os
from pathlib import Path
from typing import Optional

# 支持的文件类型
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.heif', '.raw', '.cr2', '.nef'}
VIDEO_EXTENSIONS = {'.mov', '.mp4', '.avi', '.mkv', '.webm', '.wmv', '.flv', '.m4v', '.3gp'}

# 按类型过滤的预设
FILTER_PRESETS = {
    "1": ("仅图片", IMAGE_EXTENSIONS),
    "2": ("仅视频", VIDEO_EXTENSIONS),
    "3": ("图片+视频", IMAGE_EXTENSIONS | VIDEO_EXTENSIONS),
    "4": ("全部文件", None),  # None 表示不过滤
}


def clean_path(path_str: str) -> str:
    """清理拖拽路径：去除引号、尾部空格和换行"""
    path_str = path_str.strip().strip('"').strip("'").strip()
    return path_str


def scan_files(
    path: str,
    extensions: Optional[set[str]] = None,
    recursive: bool = True,
) -> list[Path]:
    """
    扫描文件夹中的文件

    Args:
        path: 文件夹路径
        extensions: 允许的扩展名集合（None 表示不过滤）
        recursive: 是否递归扫描

    Returns:
        按文件名排序的文件路径列表
    """
    folder = Path(path)
    if not folder.exists():
        raise FileNotFoundError(f"路径不存在: {path}")
    if not folder.is_dir():
        # 用户可能拖入的是单个文件
        if folder.is_file():
            if extensions is None or folder.suffix.lower() in extensions:
                return [folder]
            return []
        raise NotADirectoryError(f"不是有效的文件夹: {path}")

    files = []
    if recursive:
        iterator = folder.rglob("*")
    else:
        iterator = folder.glob("*")

    for f in iterator:
        if f.is_file():
            if extensions is None or f.suffix.lower() in extensions:
                files.append(f)

    # 按文件名排序
    files.sort(key=lambda f: f.name.lower())
    return files


def classify_files(files: list[Path]) -> tuple[int, int]:
    """统计图片和视频数量"""
    image_count = sum(1 for f in files if f.suffix.lower() in IMAGE_EXTENSIONS)
    video_count = sum(1 for f in files if f.suffix.lower() in VIDEO_EXTENSIONS)
    return image_count, video_count