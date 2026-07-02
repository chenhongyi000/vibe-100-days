# excel-cleaner

> Vibe Coding 100 天挑战 Day 9：Excel 自动清洗器。

`excel-cleaner` 是一个本地 Excel 清洗 CLI，用来处理常见脏表格：首尾空格、单元格换行、空行、空列和重复行。它默认输出到新文件，不覆盖原表格，并可生成 JSON 清洗报告。

## 功能

- 修剪文本单元格首尾空格。
- 将单元格内换行规范为空格。
- 删除全空行。
- 删除全空列。
- 可选删除重复数据行。
- 支持多工作表逐一清洗。
- 支持 JSON 清洗报告。
- 默认不覆盖输出文件。

## 使用

基础清洗：

```bash
python src/excel_cleaner.py dirty.xlsx -o clean.xlsx
```

清洗并删除重复行：

```bash
python src/excel_cleaner.py dirty.xlsx -o clean.xlsx --dedupe
```

生成清洗报告：

```bash
python src/excel_cleaner.py dirty.xlsx -o clean.xlsx --dedupe --report clean-report.json
```

保留空行或空列：

```bash
python src/excel_cleaner.py dirty.xlsx -o clean.xlsx --keep-blank-rows --keep-blank-cols
```

## 示例输出

```text
输入: examples\dirty-orders.xlsx
输出: examples\clean-orders.xlsx
[Orders]
  修剪文本单元格: 11
  规范换行单元格: 1
  删除空行: 1
  删除空列: 1
  删除重复行: 1
报告: examples\clean-report.json
```

## 安装为命令

```bash
pip install -e .
excel-cleaner dirty.xlsx -o clean.xlsx --dedupe
```

## 测试

```bash
python -m pytest tests
```

## 项目结构

```text
day9/
├── examples/
├── src/
│   ├── __init__.py
│   └── excel_cleaner.py
├── tests/
│   └── test_excel_cleaner.py
├── README.md
├── article.md
├── pyproject.toml
└── requirements.txt
```
