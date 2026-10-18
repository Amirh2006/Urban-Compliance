"""Report builder that assembles a JSON-friendly structure from an analysis."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .. import models

REPORT_VERSION = "0.1.0"

DISCLAIMER = (
    "This report is a technical decision aid produced by Urban Compliance AI. "
    "It does not constitute an official approval or permit from any municipality. "
    "Results must be reviewed by a qualified professional before any legal use."
)

LIMITATIONS = [
    "Geometric validation uses Shapely; validity rules follow Shapely defaults.",
    "Area and perimeter are only computed when the input CRS is projected (metric).",
    "Municipal rules, regulations and zoning constraints are not evaluated in this version.",
    "The report does not query any authoritative municipal dataset.",
]

ASSUMPTIONS = [
    "Input geometries are provided in the coordinate reference system declared by the user.",
    "The system does not verify ownership or legal status of the parcel.",
]


def _utc_iso(value: datetime | None) -> str | None:
    """Serialize a datetime to an ISO string in UTC, tolerating naive values."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _collect_warnings(tests: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for test in tests:
        for warning in test.get("warnings") or []:
            warnings.append(str(warning))
    return warnings


def _collect_review_items(tests: list[dict[str, Any]]) -> list[str]:
    items: list[str] = []
    for test in tests:
        if test.get("status") in ("needs_review", "failed"):
            name = test.get("name", "unknown")
            reason = test.get("reason") or "no reason provided"
            items.append(f"{name}: {reason}")
    return items


def build_report(project: models.Project, analysis: models.Analysis) -> dict[str, Any]:
    """Assemble a JSON-friendly report for a single analysis."""
    result = analysis.result or {}
    tests = result.get("tests") or []

    files = [
        {
            "id": f.id,
            "filename": f.filename,
            "size_bytes": f.size_bytes,
            "status": f.status,
            "detected_crs": f.detected_crs,
        }
        for f in project.files
    ]

    report_id = f"RPT-{analysis.id:06d}"

    return {
        "report_id": report_id,
        "report_version": REPORT_VERSION,
        "generated_at": _utc_iso(datetime.now(timezone.utc)),
        "disclaimer": DISCLAIMER,
        "project": {
            "id": project.id,
            "name": project.name,
            "parcel_code": project.parcel_code,
            "description": project.description,
            "created_at": _utc_iso(project.created_at),
        },
        "analysis": {
            "id": analysis.id,
            "status": analysis.status,
            "engine_version": analysis.engine_version,
            "created_at": _utc_iso(analysis.created_at),
        },
        "summary": {
            "overall_status": analysis.status,
            "test_count": len(tests),
            "verified_count": sum(1 for t in tests if t.get("status") == "verified"),
            "failed_count": sum(1 for t in tests if t.get("status") == "failed"),
            "needs_review_count": sum(
                1 for t in tests if t.get("status") == "needs_review"
            ),
        },
        "files": files,
        "tests": tests,
        "warnings": _collect_warnings(tests),
        "review_items": _collect_review_items(tests),
        "assumptions": ASSUMPTIONS,
        "limitations": LIMITATIONS,
        "input_error": result.get("error"),
        "rules_applied": result.get("rules") or [],
        "sources": [],
    }