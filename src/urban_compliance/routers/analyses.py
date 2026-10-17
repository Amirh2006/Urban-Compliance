"""Analysis endpoints combining file adapters and the geometry engine."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..file_adapters.registry import parse_file
from ..geometry.engine import ENGINE_VERSION, validate_geometry

router = APIRouter(prefix="/api/v1", tags=["analyses"])


@router.post("/analyses", response_model=schemas.AnalysisOut, status_code=201)
def create_analysis(payload: schemas.AnalysisRequest, db: Session = Depends(get_db)):
    project = db.get(models.Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    analysis = models.Analysis(
        project_id=project.id,
        status="running",
        engine_version=ENGINE_VERSION,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    result_payload: dict = {"tests": []}

    geojson: dict | None = None
    crs: str | None = None

    if payload.geometry is not None:
        geojson = payload.geometry.model_dump(exclude={"crs"})
        crs = payload.geometry.crs
    elif payload.file_id is not None:
        record = db.get(models.ProjectFile, payload.file_id)
        if not record:
            analysis.status = "failed"
            result_payload["error"] = "file not found"
            analysis.result = result_payload
            db.commit()
            db.refresh(analysis)
            return analysis

        parsed = parse_file(Path(record.stored_path))
        if not parsed.ok:
            analysis.status = "failed"
            result_payload["error"] = parsed.error
            analysis.result = result_payload
            db.commit()
            db.refresh(analysis)
            return analysis

        geojson = parsed.geojson
        crs = parsed.crs
    else:
        analysis.status = "failed"
        result_payload["error"] = "geometry or file_id is required"
        analysis.result = result_payload
        db.commit()
        db.refresh(analysis)
        return analysis

    v = validate_geometry(geojson or {}, crs)
    result_payload["tests"].append(
        {
            "name": "geometry_validity",
            "status": "verified" if v.valid else "failed",
            "reason": v.reason,
            "area_m2": v.area_m2,
            "perimeter_m": v.perimeter_m,
            "crs": v.crs,
            "engine_version": v.engine_version,
            "warnings": v.warnings,
        }
    )
    analysis.status = "verified" if v.valid else "failed"
    analysis.result = result_payload
    db.commit()
    db.refresh(analysis)
    return analysis


@router.get("/analyses/{analysis_id}", response_model=schemas.AnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.get(models.Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="analysis not found")
    return analysis