"""Analysis endpoints combining file adapters, the geometry engine and rules."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..file_adapters.registry import parse_file
from ..geometry.engine import (
    ENGINE_VERSION,
    BuildingInputs,
    compute_metrics,
    validate_geometry,
)
from ..rules.registry import evaluate_all

router = APIRouter(prefix="/api/v1", tags=["analyses"])


def _aggregate_status(geometry_valid: bool, rule_results: list[dict]) -> str:
    """Aggregate a final analysis status from geometry and rule results."""
    if not geometry_valid:
        return "failed"

    if not rule_results:
        return "partial"

    statuses = {r["status"] for r in rule_results}
    if "failed" in statuses:
        return "failed"
    if "needs_review" in statuses:
        return "needs_review"
    if "verified" in statuses and statuses <= {"verified", "not_applicable"}:
        return "verified"
    return "partial"


def _building_inputs(payload: schemas.AnalysisRequest) -> BuildingInputs | None:
    """Convert the API building payload into engine-level inputs."""
    if payload.building is None:
        return None
    return BuildingInputs(
        height_m=payload.building.height_m,
        footprint_m2=payload.building.footprint_m2,
        floors=payload.building.floors,
        setback_m=payload.building.setback_m,
    )


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

    result_payload: dict = {"tests": [], "rules": []}

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

    metrics = compute_metrics(v, _building_inputs(payload))

    rule_evaluations = evaluate_all(db, metrics)
    rule_dicts = [
        {
            "rule_id": r.rule_id,
            "rule_code": r.rule_code,
            "kind": r.kind,
            "status": r.status,
            "message": r.message,
            "threshold": r.threshold,
            "actual": r.actual,
            "source_reference": r.source_reference,
            "warnings": r.warnings,
        }
        for r in rule_evaluations
    ]
    result_payload["rules"] = rule_dicts

    analysis.status = _aggregate_status(v.valid, rule_dicts)
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