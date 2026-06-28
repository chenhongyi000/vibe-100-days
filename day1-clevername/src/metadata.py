"""
元数据提取模块
优先读取 EXIF 拍摄时间，无 EXIF 时回退到文件修改时间
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Pillow 是可选依赖，未安装时自动降级
try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def _extract_exif_date(filepath: Path) -> Optional[datetime]:
    """从图片 EXIF 中提取拍摄日期"""
    if not HAS_PILLOW:
        return None

    try:
        img = Image.open(filepath)
        exif_data = img._getexif()
        if exif_data is None:
            return None

        # EXIF 标签：36867 = DateTimeOriginal, 36868 = DateTimeDigitized
        for tag_id in (36867, 36868):
            date_str = exif_data.get(tag_id)
            if date_str:
                try:
                    # EXIF 日期格式: "2024:01:15 14:00:00"
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    continue

        return None
    except Exception:
        # 图片损坏或无法读取 EXIF
        return None


def extract_date(filepath: Path) -> datetime:
    """
    提取文件的最佳日期

    优先级：
    1. EXIF DateTimeOriginal（拍摄时间）
    2. EXIF DateTimeDigitized（数字化时间）
    3. 文件修改时间（os.path.getmtime）

    Args:
        filepath: 文件路径

    Returns:
        datetime 对象
    """
    # 1. 尝试 EXIF
    exif_date = _extract_exif_date(filepath)
    if exif_date:
        return exif_date

    # 2. 回退到文件修改时间
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime)


def format_date(dt: datetime, fmt: str = "%Y-%m-%d_%H%M%S") -> str:
    """格式化日期为字符串"""
    return dt.strftime(fmt)


def get_date_source(filepath: Path) -> str:
    """返回日期来源说明（用于调试）"""
    exif_date = _extract_exif_date(filepath)
    if exif_date:
        return "EXIF拍摄时间"
    return "文件修改时间"