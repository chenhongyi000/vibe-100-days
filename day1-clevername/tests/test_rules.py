"""
规则引擎单元测试
"""

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rules import RuleEngine, FileInfo, TEMPLATES


def test_counter():
    """测试计数器生成"""
    engine = RuleEngine(counter_digits=3)
    assert engine._next_counter() == "001"
    assert engine._next_counter() == "002"
    assert engine._next_counter() == "003"

    # 测试不同位数
    engine2 = RuleEngine(counter_digits=5)
    assert engine2._next_counter() == "00001"

    print("✅ 计数器测试通过")


def test_template_apply():
    """测试模板应用"""
    engine = RuleEngine(counter_digits=3)

    fi = FileInfo(
        path=Path("/test/IMG_1234.jpg"),
        original_name="IMG_1234",
        ext=".jpg",
        date_str="2024-01-15_143022",
    )

    # 模板 1: 日期+计数器
    name = engine.apply_template(fi, TEMPLATES["1"]["template"])
    assert name == "2024-01-15_143022_001.jpg", f"Expected date_counter, got {name}"
    engine.reset_counter()

    # 模板 2: 日期+原名
    name = engine.apply_template(fi, TEMPLATES["2"]["template"])
    assert name == "2024-01-15_143022_IMG_1234.jpg", f"Expected date_original, got {name}"

    # 模板 3: AI描述+日期
    fi2 = FileInfo(
        path=Path("/test/IMG_1234.jpg"),
        original_name="IMG_1234",
        ext=".jpg",
        date_str="2024-01-15_143022",
        ai_desc="金毛犬_草地",
    )
    name = engine.apply_template(fi2, TEMPLATES["3"]["template"])
    assert name == "金毛犬_草地_2024-01-15_143022.jpg", f"Expected ai_desc_date, got {name}"

    print("✅ 模板应用测试通过")


def test_original_truncate():
    """测试原始文件名截取"""
    engine = RuleEngine(counter_digits=3)

    fi = FileInfo(
        path=Path("/test/IMG_20240115_143022.jpg"),
        original_name="IMG_20240115_143022",
        ext=".jpg",
        date_str="2024-01-15_143022",
    )

    # 自定义模板：截取前6个字符
    name = engine.apply_template(fi, "{date}_{original:6}")
    assert name == "2024-01-15_143022_IMG_20.jpg", f"Expected truncated, got {name}"

    print("✅ 原名截取测试通过")


def test_conflict_detection():
    """测试冲突检测"""
    engine = RuleEngine(counter_digits=3)

    # 创建两个会冲突的计划
    plans = [
        type("FakePlan", (), {"new_name": "same_name.jpg", "original": Path("/a/1.jpg")})(),
        type("FakePlan", (), {"new_name": "same_name.jpg", "original": Path("/b/2.jpg")})(),
        type("FakePlan", (), {"new_name": "unique.jpg", "original": Path("/c/3.jpg")})(),
    ]

    conflicts = engine.detect_conflicts(plans)
    assert len(conflicts) == 1, f"Expected 1 conflict, got {len(conflicts)}"
    assert conflicts[0].new_name == "same_name.jpg"
    assert len(conflicts[0].paths) == 2

    print("✅ 冲突检测测试通过")


def test_conflict_resolution():
    """测试冲突自动解决"""
    engine = RuleEngine(counter_digits=3)

    plans = [
        type("FakePlan", (), {"new_name": "same_name.jpg", "original": Path("/a/1.jpg")})(),
        type("FakePlan", (), {"new_name": "same_name.jpg", "original": Path("/b/2.jpg")})(),
        type("FakePlan", (), {"new_name": "same_name.jpg", "original": Path("/c/3.jpg")})(),
    ]

    resolved = engine.resolve_conflicts(plans)
    assert resolved[0].new_name == "same_name.jpg"
    assert resolved[1].new_name == "same_name_v1.jpg"
    assert resolved[2].new_name == "same_name_v2.jpg"

    print("✅ 冲突解决测试通过")


if __name__ == "__main__":
    test_counter()
    test_template_apply()
    test_original_truncate()
    test_conflict_detection()
    test_conflict_resolution()
    print("\n🎉 所有测试通过！")