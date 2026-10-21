"""Unit tests for the text chunker."""

import pytest

from urban_compliance.knowledge.chunker import chunk_pages


def test_chunk_empty_text_yields_no_chunks() -> None:
    assert chunk_pages([(1, "")]) == []


def test_chunk_short_text_yields_single_chunk() -> None:
    chunks = chunk_pages([(1, "short text")], size=800, overlap=100)
    assert len(chunks) == 1
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == "short text"


def test_chunk_long_text_produces_multiple_chunks() -> None:
    text = "alpha beta gamma delta " * 200
    chunks = chunk_pages([(1, text)], size=800, overlap=100)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.page_number == 1
        assert 0 < len(chunk.text) <= 800


def test_chunks_preserve_content() -> None:
    words = [f"word{i}" for i in range(500)]
    text = " ".join(words)
    chunks = chunk_pages([(1, text)], size=800, overlap=100)
    joined = " ".join(c.text for c in chunks)
    for word in words[:50]:
        assert word in joined


def test_chunk_preserves_page_numbers() -> None:
    chunks = chunk_pages(
        [
            (1, "first " * 200),
            (3, "third " * 200),
        ]
    )
    assert {c.page_number for c in chunks} == {1, 3}


def test_chunk_rejects_overlap_equal_to_size() -> None:
    with pytest.raises(ValueError):
        chunk_pages([(1, "some text")], size=100, overlap=100)


def test_chunk_rejects_negative_overlap() -> None:
    with pytest.raises(ValueError):
        chunk_pages([(1, "some text")], size=100, overlap=-5)