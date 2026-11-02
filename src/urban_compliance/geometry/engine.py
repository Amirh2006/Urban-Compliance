"""Shapely-based geometry validation engine.

The engine is intentionally deterministic and independent of any AI layer.
It never fabricates results: when the input CRS is missing or geographic,
metric area and perimeter are intentionally left as ``None``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shapely.errors import ShapelyError
from shapely.geometry import mapping, shape
from shapely.validation import explain_validity

from .crs import is_projected, parse_crs

ENGINE_VERSION = "0.2.0"


@dataclass
class ValidationResult:
    """Outcome of a single geometry validation run."""

    valid: bool
    reason: str | None = None
    area_m2: float | None = None
    perimeter_m: float | None = None
    crs: str | None = None
    engine_version: str = ENGINE_VERSION
    warnings: list[str] = field(default_factory=list)


@dataclass
class BuildingInputs:
    """User-supplied building characteristics for metric computation.

    All fields are optional; missing values simply mean the corresponding
    metric will not be produced, so dependent rules fall back to
    ``needs_review`` in the evaluator.
    """

    height_m: float | None = None
    footprint_m2: float | None = None
    floors: int | None = None
    setback_m: float | None = None


def _build_geometry(geojson: dict):
    """Build a Shapely geometry from a GeoJSON-like mapping."""
    try:
        return shape(geojson)
    except (ShapelyError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"input geometry cannot be parsed: {exc}") from exc


def validate_geometry(geojson: dict, crs_value: str | None) -> ValidationResult:
    """Validate a GeoJSON geometry and, when possible, compute area and perimeter.

    Area and perimeter are only computed when the CRS is projected (metric).
    For geographic CRS, a warning is returned instead of a number.
    """
    warnings: list[str] = []

    try:
        geom = _build_geometry(geojson)
    except ValueError as exc:
        return ValidationResult(valid=False, reason=str(exc), crs=crs_value)

    if geom.is_empty:
        return ValidationResult(valid=False, reason="geometry is empty", crs=crs_value)

    if not geom.is_valid:
        return ValidationResult(
            valid=False,
            reason=f"geometry is invalid: {explain_validity(geom)}",
            crs=crs_value,
        )

    crs = parse_crs(crs_value)
    if crs is None:
        warnings.append("CRS is missing or cannot be parsed; area and perimeter were not computed.")
        return ValidationResult(valid=True, crs=None, warnings=warnings)

    if not is_projected(crs):
        warnings.append(
            "CRS is geographic; metric area requires reprojection to a projected CRS."
        )
        return ValidationResult(valid=True, crs=crs.to_string(), warnings=warnings)

    return ValidationResult(
        valid=True,
        area_m2=float(geom.area),
        perimeter_m=float(geom.length),
        crs=crs.to_string(),
        warnings=warnings,
    )


def compute_metrics(
    validation: ValidationResult,
    building: BuildingInputs | None = None,
) -> dict[str, float | str | None]:
    """Assemble the metrics dict consumed by the rule evaluator.

    Parcel metrics (area, perimeter) come from ``validation``. Building
    metrics (height, setback) come from ``building`` when supplied. Derived
    ratios (coverage, FAR) are computed only when both the parcel area and
    the required building fields are available; otherwise they are omitted
    so that dependent rules fall back to ``needs_review``.
    """
    metrics: dict[str, float | str | None] = {
        "area_m2": validation.area_m2,
        "perimeter_m": validation.perimeter_m,
        "crs": validation.crs,
    }

    if building is None:
        return metrics

    if building.height_m is not None:
        metrics["height_m"] = float(building.height_m)
    if building.setback_m is not None:
        metrics["setback_m"] = float(building.setback_m)

    area = validation.area_m2
    footprint = building.footprint_m2
    if footprint is not None and area:
        metrics["coverage_ratio"] = float(footprint) / float(area)
        if building.floors is not None and building.floors >= 1:
            metrics["far_ratio"] = (float(footprint) * building.floors) / float(area)

    return metrics


def geometry_to_geojson(geom) -> dict:
    """Serialize a Shapely geometry back to a GeoJSON-like mapping."""
    return mapping(geom)