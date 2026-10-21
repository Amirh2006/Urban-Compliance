"""Knowledge source ingestion, listing and search endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..db import get_db
from ..knowledge.chunker import chunk_pages
from ..knowledge.pdf_extractor import extract_pdf
from ..knowledge.search import search_chunks

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


def _safe_filename(name: str) -> str:
    return Path(name).name.replace("\x00", "_") or "document.pdf"


@router.post("/sources", response_model=schemas.KnowledgeSourceOut, status_code=201)
def create_source(
    payload: schemas.KnowledgeSourceCreate,
    db: Session = Depends(get_db),
):
    source = models.KnowledgeSource(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/sources", response_model=list[schemas.KnowledgeSourceOut])
def list_sources(db: Session = Depends(get_db)):
    return (
        db.query(models.KnowledgeSource)
        .order_by(models.KnowledgeSource.id.desc())
        .all()
    )


@router.get("/sources/{source_id}", response_model=schemas.KnowledgeSourceDetail)
def get_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(models.KnowledgeSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="knowledge source not found")
    return source


@router.patch("/sources/{source_id}/verify", response_model=schemas.KnowledgeSourceOut)
def verify_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(models.KnowledgeSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="knowledge source not found")
    source.is_verified = True
    db.commit()
    db.refresh(source)
    return source


@router.post(
    "/sources/{source_id}/document",
    response_model=schemas.KnowledgeSourceOut,
)
def upload_document(
    source_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF for a knowledge source and extract its text."""
    source = db.get(models.KnowledgeSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="knowledge source not found")

    safe = _safe_filename(file.filename or "document.pdf")
    target_dir = settings.data_dir / "knowledge" / str(source_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / safe

    max_bytes = settings.max_upload_mb * 1024 * 1024
    size = 0
    with target.open("wb") as out:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                out.close()
                target.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413, detail="upload exceeds configured size limit"
                )
            out.write(chunk)

    source.filename = safe
    source.stored_path = str(target)
    source.size_bytes = size

    # Clear any previous chunks before re-ingesting.
    db.query(models.KnowledgeChunk).filter(
        models.KnowledgeChunk.source_id == source.id
    ).delete(synchronize_session=False)

    extraction = extract_pdf(target)
    if not extraction.ok:
        source.extraction_status = "failed"
        source.extraction_error = extraction.error
        source.page_count = 0
        db.commit()
        db.refresh(source)
        return source

    chunk_records = chunk_pages(
        [(page.number, page.text) for page in extraction.pages]
    )
    for chunk in chunk_records:
        db.add(
            models.KnowledgeChunk(
                source_id=source.id,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                char_count=len(chunk.text),
            )
        )

    source.page_count = len(extraction.pages)
    source.extraction_status = "parsed"
    source.extraction_error = None
    db.commit()
    db.refresh(source)
    return source


@router.get("/search", response_model=list[schemas.KnowledgeSearchHit])
def search(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    hits = search_chunks(db, q, limit=limit)
    return [
        schemas.KnowledgeSearchHit(
            chunk_id=h.chunk_id,
            source_id=h.source_id,
            source_title=h.source_title,
            page_number=h.page_number,
            chunk_index=h.chunk_index,
            snippet=h.snippet,
        )
        for h in hits
    ]