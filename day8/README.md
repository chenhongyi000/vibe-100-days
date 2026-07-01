# pdf-kit-lite

> Vibe Coding 100 天挑战 Day 8：PDF 拆分合并工具。

`pdf-kit-lite` 是一个本地 PDF 工具，可以查看页数、合并多个 PDF、按页码范围拆分 PDF。它不需要登录、不上传文件到云端，适合处理合同、发票、简历、资料包等日常文档。

## 功能

- 查看 PDF 页数。
- 按传入顺序合并多个 PDF。
- 逐页拆分 PDF。
- 按页码范围拆分 PDF，例如 `1-3,5,-1`。
- 支持倒数页码，`-1` 表示最后一页。
- 默认不覆盖输出文件，合并时需要 `--overwrite` 才会覆盖。
- 暂不处理加密 PDF，避免静默失败。

## 使用

查看页数：

```bash
python src/pdf_kit_lite.py info a.pdf b.pdf
```

合并 PDF：

```bash
python src/pdf_kit_lite.py merge a.pdf b.pdf -o merged.pdf
```

拆成单页：

```bash
python src/pdf_kit_lite.py split merged.pdf -o split-pages
```

按范围拆分：

```bash
python src/pdf_kit_lite.py split merged.pdf -o split-pages -r 1-3,5,-1
```

## 示例输出

```text
examples\input\contract-a.pdf: 2 页
examples\input\invoice-b.pdf: 3 页
```

```text
已合并 2 个 PDF，共 5 页 -> examples\output\merged.pdf
```

```text
已输出 2 个 PDF 到 examples\output\split
- examples\output\split\demo_p1-2.pdf
- examples\output\split\demo_p5-5.pdf
```

## 安装为命令

```bash
pip install -e .
pdf-kit-lite info a.pdf
```

## 测试

```bash
python -m pytest tests
```

## 项目结构

```text
day8/
├── examples/
│   ├── input/
│   └── output/
├── src/
│   ├── __init__.py
│   └── pdf_kit_lite.py
├── tests/
│   └── test_pdf_kit_lite.py
├── README.md
├── article.md
├── pyproject.toml
└── requirements.txt
```
