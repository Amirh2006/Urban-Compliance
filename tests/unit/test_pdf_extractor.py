"""Unit tests for the PDF extractor."""

from pathlib import Path

from urban_compliance.knowledge.pdf_extractor import extract_pdf


def test_extract_pdf_returns_error_for_missing_file(tmp_path: Path) -> None:
    result = extract_pdf(tmp_path / "missing.pdf")
    assert result.ok is False
    assert "not found" in (result.error or "")


def test_extract_pdf_returns_error_for_invalid_pdf(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a real pdf")

    result = extract_pdf(bad)
    assert result.ok is False
    assert result.error


def test_extract_pdf_reads_pages_with_mocked_reader(
    tmp_path: Path, monkeypatch
) -> None:
    pdf_path = tmp_path / "fake.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    class FakePage:
        def __init__(self, text: str):
            self._text = text

        def extract_text(self) -> str:
            return self._text

    class FakeReader:
        def __init__(self, path: str):
            self.pages = [FakePage("page one"), FakePage("page two")]

    monkeypatch.setattr(
        "urban_compliance.knowledge.pdf_extractor.PdfReader", FakeReader
    )

    result = extract_pdf(pdf_path)
    assert result.ok is True
    assert len(result.pages) == 2
    assert result.pages[0].number == 1
    assert result.pages[0].text == "page one"
    assert result.pages[1].number == 2
    assert result.pages[1].text == "page two"