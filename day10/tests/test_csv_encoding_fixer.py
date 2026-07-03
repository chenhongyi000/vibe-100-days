import json
from pathlib import Path

from src.csv_encoding_fixer import detect_encoding, fix_csv_encoding, main


def test_detect_utf8_sig():
    assert detect_encoding("姓名,城市\n".encode("utf-8-sig")) == "utf-8-sig"


def test_fix_gbk_csv_to_utf8_sig(tmp_path: Path):
    source = tmp_path / "gbk.csv"
    output = tmp_path / "utf8.csv"
    source.write_bytes("姓名,城市\n张三,上海\n".encode("gbk"))

    result = fix_csv_encoding(source, output, source_encoding="gbk")

    assert result.source_encoding == "gbk"
    assert result.rows == 2
    assert result.columns == 2
    assert output.read_text(encoding="utf-8-sig") == "姓名,城市\n张三,上海\n"
    assert output.read_bytes().startswith(b"\xef\xbb\xbf")


def test_report_written(tmp_path: Path):
    source = tmp_path / "gbk.csv"
    output = tmp_path / "utf8.csv"
    report = tmp_path / "report.json"
    source.write_bytes("姓名,城市\n李四,北京\n".encode("gbk"))

    fix_csv_encoding(source, output, source_encoding="gbk", report_path=report)

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["rows"] == 2
    assert payload["columns"] == 2
    assert payload["target_encoding"] == "utf-8-sig"


def test_no_overwrite_by_default(tmp_path: Path):
    source = tmp_path / "a.csv"
    output = tmp_path / "out.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    output.write_text("exists", encoding="utf-8")

    try:
        fix_csv_encoding(source, output)
    except FileExistsError:
        assert True
    else:
        raise AssertionError("expected FileExistsError")


def test_cli_runs(tmp_path: Path):
    source = tmp_path / "gbk.csv"
    output = tmp_path / "utf8.csv"
    source.write_bytes("姓名,城市\n王五,深圳\n".encode("gbk"))

    assert main([str(source), "-o", str(output), "--from-encoding", "gbk"]) == 0
    assert "王五" in output.read_text(encoding="utf-8-sig")
