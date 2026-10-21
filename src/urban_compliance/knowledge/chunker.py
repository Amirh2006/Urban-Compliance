"""Split extracted page text into overlapping chunks for search."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_CHUNK_SIZE = 800
DEFAULT_OVERLAP = 100


@dataclass
class TextChunk:
    """A single chunk of text belonging to a specific page."""

    page_number: int
    chunk_index: int
    text: str


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping pieces, preferring word boundaries."""
    text = text.strip()
    if not text:
        return []

    if size <= 0:
        raise ValueError("chunk size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be non-negative and smaller than size")

    pieces: list[str] = []
    n = len(text)
    start = 0

    while start < n:
        end = min(start + size, n)

        if end < n:
            # Try to break at a word boundary for readability.
            space_pos = text.rfind(" ", start + overlap, end)
            if space_pos > start:
                end = space_pos

        pieces.append(text[start:end])

        if end >= n:
            break

        next_start = end - overlap
        if next_start <= start:
            next_start = end
        start = next_start

    return pieces


def chunk_pages(
    pages: list[tuple[int, str]],
    *,
    size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[TextChunk]:
    """Chunk every page and return a flat list of TextChunk.

    ``pages`` is an iterable of ``(page_number, text)`` pairs.
    """
    result: list[TextChunk] = []
    for page_number, text in pages:
        for index, piece in enumerate(_split_text(text, size, overlap)):
            result.append(
                TextChunk(page_number=page_number, chunk_index=index, text=piece)
            )
    return result