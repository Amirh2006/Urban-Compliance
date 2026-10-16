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

ENGINE_VERSION = "0.1.0"


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


def geometry_to_geojson(geom) -> dict:
    """Serialize a Shapely geometry back to a GeoJSON-like mapping."""
    return mapping(geom)