"""Simple substring search over indexed knowledge chunks."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .. import models


@dataclass
class SearchHit:
    """A single search result pointing to a chunk."""

    chunk_id: int
    source_id: int
    source_title: str
    page_number: int
    chunk_index: int
    snippet: str


def search_chunks(
    db: Session,
    query: str,
    *,
    limit: int = 20,
    snippet_radius: int = 120,
) -> list[SearchHit]:
    """Return chunks whose text contains ``query`` (case-insensitive)."""
    query = (query or "").strip()
    if not query:
        return []

    like_pattern = f"%{query}%"
    rows = (
        db.query(models.KnowledgeChunk, models.KnowledgeSource)
        .join(
            models.KnowledgeSource,
            models.KnowledgeChunk.source_id == models.KnowledgeSource.id,
        )
        .filter(models.KnowledgeChunk.text.ilike(like_pattern))
        .order_by(
            models.KnowledgeSource.id.asc(),
            models.KnowledgeChunk.page_number.asc(),
            models.KnowledgeChunk.chunk_index.asc(),
        )
        .limit(limit)
        .all()
    )

    hits: list[SearchHit] = []
    for chunk, source in rows:
        hits.append(
            SearchHit(
                chunk_id=chunk.id,
                source_id=source.id,
                source_title=source.title,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                snippet=_make_snippet(chunk.text, query, snippet_radius),
            )
        )
    return hits


def _make_snippet(text: str, query: str, radius: int) -> str:
    """Return a snippet centered around the query match."""
    idx = text.lower().find(query.lower())
    if idx < 0:
        return text[: radius * 2]
    start = max(0, idx - radius)
    end = min(len(text), idx + len(query) + radius)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"