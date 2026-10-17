"""Report endpoint for completed analyses."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..reporting.report_builder import build_report

router = APIRouter(prefix="/api/v1", tags=["reports"])


@router.get("/analyses/{analysis_id}/report", response_model=schemas.ReportOut)
def get_report(analysis_id: int, db: Session = Depends(get_db)):
    """Return a JSON report for the given analysis."""
    analysis = db.get(models.Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="analysis not found")

    project = db.get(models.Project, analysis.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    return build_report(project, analysis)