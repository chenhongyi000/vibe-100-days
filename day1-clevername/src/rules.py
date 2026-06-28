"""
规则引擎模块
负责命名模板解析、token 替换、冲突检测
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .metadata import extract_date, format_date


@dataclass
class FileInfo:
    """文件信息数据类"""

    path: Path
    original_name: str  # 不含扩展名的文件名
    ext: str  # 扩展名（含点）
    date_str: str  # 格式化后的日期字符串
    ai_desc: str = ""  # AI 语义标签（P1 功能）


@dataclass
class RenamePlan:
    """重命名计划"""

    original: Path
    new_name: str  # 新文件名（含扩展名）
    new_path: Path = field(init=False)

    def __post_init__(self):
        self.new_path = self.original.parent / self.new_name


@dataclass
class Conflict:
    """文件名冲突"""

    new_name: str
    paths: list[Path]  # 冲突的原始文件路径列表


# 内置模板定义
TEMPLATES = {
    "1": {
        "name": "日期_计数器",
        "template": "{date}_{counter}",
        "example": "2024-01-15_143022_001.jpg",
        "description": "按拍摄时间排序，自动编号，适合整理照片",
    },
    "2": {
        "name": "日期_原名",
        "template": "{date}_{original}",
        "example": "2024-01-15_143022_IMG_1234.jpg",
        "description": "保留原始文件名，前面加上拍摄日期",
    },
    "3": {
        "name": "AI描述_日期",
        "template": "{ai_desc}_{date}",
        "example": "金毛犬_草地_2024-01-15_143022.jpg",
        "description": "AI 识别图片内容作为文件名（需配置 AI）",
    },
}


class RuleEngine:
    """命名规则引擎"""

    def __init__(self, counter_digits: int = 3):
        self.counter_digits = counter_digits
        self._counter = 0

    def reset_counter(self):
        """重置计数器"""
        self._counter = 0

    def _next_counter(self) -> str:
        """生成下一个计数器值（自动补零）"""
        self._counter += 1
        return str(self._counter).zfill(self.counter_digits)

    def build_file_info(self, filepath: Path) -> FileInfo:
        """
        从文件路径构建 FileInfo

        Args:
            filepath: 文件路径

        Returns:
            FileInfo 对象
        """
        dt = extract_date(filepath)
        date_str = format_date(dt)
        original_name = filepath.stem  # 不含扩展名
        ext = filepath.suffix.lower()  # 含点的小写扩展名

        return FileInfo(
            path=filepath,
            original_name=original_name,
            ext=ext,
            date_str=date_str,
        )

    def apply_template(
        self,
        file_info: FileInfo,
        template: str,
        counter: Optional[int] = None,
    ) -> str:
        """
        应用命名模板生成新文件名

        Args:
            file_info: 文件信息
            template: 模板字符串，如 "{date}_{counter}"
            counter: 指定计数器值（None 则自动递增）

        Returns:
            新文件名（含扩展名）
        """
        name = template

        # 替换 {date}
        name = name.replace("{date}", file_info.date_str)

        # 替换 {counter}
        cnt = self._next_counter() if counter is None else str(counter).zfill(self.counter_digits)
        name = name.replace("{counter}", cnt)

        # 替换 {original:N}（截取前 N 个字符）
        name = re.sub(
            r"\{original:(\d+)\}",
            lambda m: file_info.original_name[: int(m.group(1))],
            name,
        )

        # 替换 {original}
        name = name.replace("{original}", file_info.original_name)

        # 替换 {ai_desc}
        name = name.replace("{ai_desc}", file_info.ai_desc if file_info.ai_desc else "未识别")

        # 替换 {ext}
        name = name.replace("{ext}", file_info.ext)

        return name + file_info.ext if "{ext}" not in template else name

    def generate_plan(
        self,
        files: list[Path],
        template: str,
    ) -> list[RenamePlan]:
        """
        生成完整重命名计划

        Args:
            files: 文件路径列表
            template: 命名模板

        Returns:
            RenamePlan 列表
        """
        self.reset_counter()
        plans = []

        # 按日期排序，确保计数器顺序合理
        file_infos = [self.build_file_info(f) for f in files]
        file_infos.sort(key=lambda fi: (fi.date_str, fi.original_name))

        for fi in file_infos:
            new_name = self.apply_template(fi, template)
            plans.append(RenamePlan(original=fi.path, new_name=new_name))

        return plans

    def detect_conflicts(self, plans: list[RenamePlan]) -> list[Conflict]:
        """
        检测文件名冲突

        Args:
            plans: 重命名计划列表

        Returns:
            冲突列表
        """
        name_map: dict[str, list[Path]] = {}
        for plan in plans:
            key = plan.new_name.lower()
            if key not in name_map:
                name_map[key] = []
            name_map[key].append(plan.original)

        conflicts = []
        for name, paths in name_map.items():
            if len(paths) > 1:
                conflicts.append(Conflict(new_name=name, paths=paths))

        return conflicts

    def resolve_conflicts(self, plans: list[RenamePlan]) -> list[RenamePlan]:
        """
        自动解决冲突：重复文件名追加 _v1, _v2...

        Args:
            plans: 重命名计划列表

        Returns:
            解决冲突后的计划列表
        """
        seen: dict[str, int] = {}
        resolved = []

        for plan in plans:
            key = plan.new_name.lower()
            if key in seen:
                seen[key] += 1
                # 在扩展名前插入 _vN
                stem = Path(plan.new_name).stem
                ext = Path(plan.new_name).suffix
                plan.new_name = f"{stem}_v{seen[key]}{ext}"
            else:
                seen[key] = 0
            resolved.append(plan)

        return resolved