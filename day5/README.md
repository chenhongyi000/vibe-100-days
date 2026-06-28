# wechat-md

> Vibe Coding 100 天挑战 Day 5：Markdown 转公众号排版工具。

`wechat-md` 是一个零依赖命令行工具，可以把 Markdown 转成适合微信公众号编辑器的内联样式 HTML。

## 功能

- 支持 YAML-like frontmatter，并自动读取 `title`。
- 支持标题、段落、引用、无序列表、有序列表、分割线。
- 支持行内代码、粗体、斜体、链接和图片。
- 支持围栏代码块，并自动转义 HTML 特殊字符。
- 支持 Markdown 表格。
- 支持完整 HTML 预览页和正文片段两种输出模式。

## 使用

```bash
python src/wechat_md.py examples/sample_article.md -o examples/sample_article.html
```

只输出可复制到公众号编辑器的正文片段：

```bash
python src/wechat_md.py examples/sample_article.md --body-only -o examples/sample_body.html
```

直接打印到终端：

```bash
python src/wechat_md.py examples/sample_article.md
```

## 安装为命令

```bash
pip install -e .
wechat-md examples/sample_article.md -o examples/sample_article.html
```

## 测试

```bash
python -m pytest tests
```

## 项目结构

```text
day5/
├── examples/
│   └── sample_article.md
├── src/
│   ├── __init__.py
│   └── wechat_md.py
├── tests/
│   └── test_wechat_md.py
├── README.md
├── article.md
├── pyproject.toml
└── requirements.txt
```
