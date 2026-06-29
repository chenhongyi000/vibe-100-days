from pathlib import Path

from PIL import Image

from src.img_slim import (
    CompressOptions,
    build_output_path,
    calculate_target_size,
    compress_batch,
    find_images,
    main,
)


def make_image(path: Path, size: tuple[int, int] = (1200, 800), color=(80, 120, 180)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, color)
    image.save(path, quality=95)


def test_find_images_non_recursive(tmp_path: Path):
    make_image(tmp_path / "a.jpg")
    make_image(tmp_path / "nested" / "b.jpg")
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")

    images = find_images(tmp_path, recursive=False)

    assert images == [tmp_path / "a.jpg"]


def test_find_images_recursive(tmp_path: Path):
    make_image(tmp_path / "a.jpg")
    make_image(tmp_path / "nested" / "b.webp")

    images = find_images(tmp_path, recursive=True)

    assert images == [tmp_path / "a.jpg", tmp_path / "nested" / "b.webp"]


def test_calculate_target_size_without_upscaling():
    assert calculate_target_size(800, 600, 1600, None) == (800, 600)


def test_calculate_target_size_by_width():
    assert calculate_target_size(3200, 1800, 1600, None) == (1600, 900)


def test_build_output_path_preserves_relative_directory(tmp_path: Path):
    source = tmp_path / "input" / "nested" / "a.png"
    options = CompressOptions(
        input_path=tmp_path / "input",
        output_dir=tmp_path / "output",
        recursive=True,
    )

    assert build_output_path(source, options) == tmp_path / "output" / "nested" / "a.png"


def test_compress_batch_writes_smaller_resized_image(tmp_path: Path):
    source = tmp_path / "input" / "large.jpg"
    output_dir = tmp_path / "output"
    make_image(source, size=(2400, 1600))

    results = compress_batch(
        CompressOptions(
            input_path=source.parent,
            output_dir=output_dir,
            quality=70,
            max_width=800,
        )
    )

    assert len(results) == 1
    result = results[0]
    assert result.status == "compressed"
    assert result.output.exists()
    assert result.output_size == (800, 533)
    with Image.open(result.output) as image:
        assert image.size == (800, 533)


def test_dry_run_does_not_write_file(tmp_path: Path):
    source = tmp_path / "a.jpg"
    output_dir = tmp_path / "output"
    make_image(source)

    results = compress_batch(
        CompressOptions(
            input_path=source,
            output_dir=output_dir,
            dry_run=True,
        )
    )

    assert results[0].status == "dry-run"
    assert not results[0].output.exists()


def test_report_is_written(tmp_path: Path):
    source = tmp_path / "a.jpg"
    report = tmp_path / "report.csv"
    make_image(source)

    compress_batch(
        CompressOptions(
            input_path=source,
            output_dir=tmp_path / "output",
            report_path=report,
        )
    )

    text = report.read_text(encoding="utf-8")
    assert "source,output,status" in text
    assert "compressed" in text


def test_cli_rejects_invalid_quality(tmp_path: Path):
    source = tmp_path / "a.jpg"
    make_image(source)

    try:
        main([str(source), "--quality", "101"])
    except SystemExit as exc:
        assert exc.code == 2
