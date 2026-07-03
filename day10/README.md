# csv-encoding-fixer

CSV encoding fixer for Day 10 of the Vibe Coding 100 days challenge.

It detects common CSV encodings, converts files to an Excel-friendly target encoding, and writes a small report so you know what changed.

## Features

- Detects UTF-8 BOM, UTF-8, GB18030, GBK, Big5, cp1252, and latin1.
- Uses `charset-normalizer` as an optional fallback detector.
- Converts CSV files to `utf-8-sig` by default for better Windows Excel compatibility.
- Supports manual source encoding with `--from-encoding`.
- Sniffs delimiter, row count, and column count after decoding.
- Writes a JSON report with encoding and CSV shape details.
- Refuses to overwrite output files unless `--overwrite` is passed.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Usage

```powershell
python src\csv_encoding_fixer.py examples\orders-gbk.csv -o examples\orders-utf8.csv --from-encoding gbk --report examples\encoding-report.json --overwrite
```

Example output:

```text
输入: examples\orders-gbk.csv
输出: examples\orders-utf8.csv
源编码: gbk
目标编码: utf-8-sig
行数: 4
列数: 3
分隔符: ','
替换错误字符: 否
报告: examples\encoding-report.json
```

## CLI

```powershell
python src\csv_encoding_fixer.py <input.csv> -o <output.csv>
```

Useful options:

- `--from-encoding gbk`: force a source encoding when auto detection is uncertain.
- `--to-encoding utf-8-sig`: choose the target encoding.
- `--report report.json`: write a conversion report.
- `--overwrite`: allow replacing an existing output file.

## Test

```powershell
python -m pytest tests
```

## Project Structure

```text
day10/
  src/
    csv_encoding_fixer.py
  tests/
    test_csv_encoding_fixer.py
  examples/
    orders-gbk.csv
    orders-utf8.csv
    encoding-report.json
  README.md
  requirements.txt
  pyproject.toml
```
