# img-slim

> Vibe Coding 100 天挑战 Day 6：批量图片压缩器。

`img-slim` 是一个面向内容创作者的批量图片压缩 CLI。它可以递归扫描图片目录，按最长边缩放并压缩 JPG、PNG、WebP，输出压缩报告，适合公众号、博客、知识库和素材归档。

## 功能

- 支持 JPG、PNG、WebP。
- 支持单文件或目录批量处理。
- 支持递归扫描子目录。
- 默认输出到 `compressed/`，不覆盖原图。
- 支持按最大宽度、最大高度等比例缩放。
- 支持 JPEG/WebP 质量参数。
- 支持统一转 JPG。
- 支持 dry-run 预演。
- 支持 CSV 压缩报告。

## 使用

压缩一个目录：

```bash
python src/img_slim.py examples/input -o examples/output --max-width 1000 --quality 76 --report examples/report.csv
```

递归压缩子目录：

```bash
python src/img_slim.py D:/photos -o D:/photos-compressed --recursive
```

只预演，不写入文件：

```bash
python src/img_slim.py D:/photos --dry-run
```

统一输出为 JPG：

```bash
python src/img_slim.py D:/photos -o D:/jpg-output --to-jpg
```

## 示例结果

本项目示例图片压缩结果：

```text
扫描图片: 2
已压缩: 2  跳过: 0  失败: 0  预演: 0
原始大小: 111.0 KB
输出大小: 16.3 KB
节省空间: 94.7 KB (85.3%)
```

## 安装为命令

```bash
pip install -e .
img-slim examples/input -o examples/output
```

## 测试

```bash
python -m pytest tests
```

## 项目结构

```text
day6/
├── examples/
│   ├── input/
│   ├── output/
│   └── report.csv
├── src/
│   ├── __init__.py
│   └── img_slim.py
├── tests/
│   └── test_img_slim.py
├── README.md
├── article.md
├── pyproject.toml
└── requirements.txt
```
