"""File upload and processing endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..db import get_db
from ..file_adapters.registry import get_adapter, parse_file

router = APIRouter(prefix="/api/v1", tags=["files"])


def _safe_filename(name: str) -> str:
    """Return a filename stripped of any path components."""
    return Path(name).name.replace("\x00", "_") or "upload.bin"


@router.post(
    "/projects/{project_id}/files",
    response_model=schemas.FileOut,
    status_code=201,
)
def upload_file(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    safe = _safe_filename(file.filename or "upload.bin")
    target_dir = settings.data_dir / "uploads" / str(project_id)
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

    record = models.ProjectFile(
        project_id=project_id,
        filename=safe,
        content_type=file.content_type,
        size_bytes=size,
        stored_path=str(target),
        status="uploaded",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/files/{file_id}", response_model=schemas.FileOut)
def get_file(file_id: int, db: Session = Depends(get_db)):
    record = db.get(models.ProjectFile, file_id)
    if not record:
        raise HTTPException(status_code=404, detail="file not found")
    return record


@router.post("/files/{file_id}/process", response_model=schemas.FileOut)
def process_file(file_id: int, db: Session = Depends(get_db)):
    record = db.get(models.ProjectFile, file_id)
    if not record:
        raise HTTPException(status_code=404, detail="file not found")

    path = Path(record.stored_path)
    if not path.exists():
        record.status = "failed"
        record.error = "stored file is missing on disk"
        db.commit()
        db.refresh(record)
        return record

    if get_adapter(path) is None:
        record.status = "unsupported"
        record.error = f"unsupported file extension: {path.suffix}"
        db.commit()
        db.refresh(record)
        return record

    result = parse_file(path)
    if not result.ok:
        record.status = "failed"
        record.error = result.error
    else:
        record.status = "parsed"
        record.error = None
        record.detected_crs = result.crs
    db.commit()
    db.refresh(record)
    return record