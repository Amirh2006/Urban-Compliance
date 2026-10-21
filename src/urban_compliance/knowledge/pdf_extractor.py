"""Extract text from PDF files using pypdf."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader


@dataclass
class PageText:
    """Text extracted from a single page."""

    number: int
    text: str


@dataclass
class PdfExtractionResult:
    """Outcome of extracting text from a PDF file."""

    ok: bool
    pages: list[PageText] = field(default_factory=list)
    error: str | None = None


def extract_pdf(path: Path) -> PdfExtractionResult:
    """Extract per-page text from a PDF file.

    A missing or unreadable file returns ``ok=False`` with an error message.
    Individual empty pages are preserved with empty text so the caller can
    decide whether to surface them as warnings.
    """
    if not path.exists():
        return PdfExtractionResult(ok=False, error="file not found")

    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # noqa: BLE001
        return PdfExtractionResult(ok=False, error=f"failed to open PDF: {exc}")

    try:
        pages: list[PageText] = []
        for index, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:  # noqa: BLE001
                # A single broken page must not abort the whole document.
                text = ""
            pages.append(PageText(number=index, text=text))
    except Exception as exc:  # noqa: BLE001
        return PdfExtractionResult(ok=False, error=f"failed to extract text: {exc}")

    return PdfExtractionResult(ok=True, pages=pages)