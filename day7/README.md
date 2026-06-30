# dupe-scout

> Vibe Coding 100 天挑战 Day 7：文件夹重复文件扫描器。

`dupe-scout` 是一个安全的重复文件扫描 CLI。它先按文件大小筛选候选文件，再用 SHA-256 哈希确认内容是否真的一致，帮助你找出下载目录、照片备份、资料库里的重复文件。

## 功能

- 按文件内容识别重复文件，不靠文件名猜测。
- 先按大小分组，再计算 SHA-256，减少无意义读盘。
- 默认跳过隐藏目录、`.git`、缓存目录和虚拟环境。
- 支持最小文件大小过滤，例如 `--min-size 1mb`。
- 支持额外忽略规则，例如 `--ignore *.tmp`。
- 支持 JSON 和 CSV 报告。
- 默认只扫描和报告，不删除文件。

## 使用

扫描一个文件夹：

```bash
python src/dupe_scout.py D:/Downloads
```

只扫描大于 1MB 的文件：

```bash
python src/dupe_scout.py D:/Downloads --min-size 1mb
```

输出 JSON 和 CSV 报告：

```bash
python src/dupe_scout.py D:/Downloads --json dupes.json --csv dupes.csv
```

忽略临时文件：

```bash
python src/dupe_scout.py D:/Downloads --ignore *.tmp --ignore cache
```

## 示例结果

```text
扫描目录: examples\sample-folder
扫描文件: 5
候选文件: 4
重复组数: 2
重复文件: 4
可释放空间: 76 B

[1] 2 个文件 | 单个 40 B | 可释放 40 B
    - backup\photo-a-copy.jpg
    - photo-a.jpg
[2] 2 个文件 | 单个 36 B | 可释放 36 B
    - backup\invoice-copy.txt
    - downloads\invoice-2026.txt
```

## 安装为命令

```bash
pip install -e .
dupe-scout D:/Downloads --min-size 1mb
```

## 测试

```bash
python -m pytest tests
```

## 项目结构

```text
day7/
├── examples/
│   ├── sample-folder/
│   └── reports/
├── src/
│   ├── __init__.py
│   └── dupe_scout.py
├── tests/
│   └── test_dupe_scout.py
├── README.md
├── article.md
├── pyproject.toml
└── requirements.txt
```
