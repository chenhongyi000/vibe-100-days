from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from src.pdf_kit_lite import PageRange, main, merge_pdfs, parse_ranges, read_pdf_info, split_pdf


def make_pdf(path: Path, pages: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = canvas.Canvas(str(path))
    for page in range(1, pages + 1):
        doc.drawString(72, 720, f"{path.stem} page {page}")
        doc.showPage()
    doc.save()


def page_count(path: Path) -> int:
    return len(PdfReader(str(path)).pages)


def test_read_pdf_info(tmp_path: Path):
    pdf = tmp_path / "a.pdf"
    make_pdf(pdf, 3)

    info = read_pdf_info(pdf)

    assert info.pages == 3
    assert info.encrypted is False


def test_merge_pdfs(tmp_path: Path):
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    output = tmp_path / "merged.pdf"
    make_pdf(a, 2)
    make_pdf(b, 3)

    total = merge_pdfs([a, b], output)

    assert total == 5
    assert page_count(output) == 5


def test_split_pdf_into_single_pages(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    out = tmp_path / "out"
    make_pdf(pdf, 3)

    outputs = split_pdf(pdf, out)

    assert len(outputs) == 3
    assert [page_count(path) for path in outputs] == [1, 1, 1]


def test_split_pdf_with_ranges(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    out = tmp_path / "out"
    make_pdf(pdf, 5)

    outputs = split_pdf(pdf, out, ranges=[PageRange(1, 2), PageRange(-1, -1)])

    assert len(outputs) == 2
    assert page_count(outputs[0]) == 2
    assert page_count(outputs[1]) == 1


def test_parse_ranges():
    ranges = parse_ranges("1-3,5,-1")

    assert ranges == [PageRange(1, 3), PageRange(5, 5), PageRange(-1, -1)]


def test_cli_info(tmp_path: Path, capsys):
    pdf = tmp_path / "a.pdf"
    make_pdf(pdf, 2)

    assert main(["info", str(pdf)]) == 0
    captured = capsys.readouterr()
    assert "2 页" in captured.out


def test_cli_merge_requires_two_files(tmp_path: Path):
    pdf = tmp_path / "a.pdf"
    make_pdf(pdf, 1)

    assert main(["merge", str(pdf), "-o", str(tmp_path / "out.pdf")]) == 1
