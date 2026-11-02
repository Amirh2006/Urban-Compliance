"""Unit tests for the geometry validation engine."""

import pytest

from urban_compliance.geometry.engine import (
    BuildingInputs,
    ValidationResult,
    compute_metrics,
    validate_geometry,
)


def test_valid_polygon_with_projected_crs() -> None:
    geojson = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
    }
    result = validate_geometry(geojson, "EPSG:3857")
    assert result.valid is True
    assert result.area_m2 == pytest.approx(100.0)
    assert result.perimeter_m == pytest.approx(40.0)
    assert result.crs is not None


def test_self_intersecting_polygon_is_invalid() -> None:
    geojson = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [10, 10], [10, 0], [0, 10], [0, 0]]],
    }
    result = validate_geometry(geojson, "EPSG:3857")
    assert result.valid is False
    assert result.reason is not None
    assert "invalid" in result.reason.lower()


def test_missing_crs_returns_warning_and_no_area() -> None:
    geojson = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    }
    result = validate_geometry(geojson, None)
    assert result.valid is True
    assert result.area_m2 is None
    assert result.perimeter_m is None
    assert len(result.warnings) >= 1


def test_geographic_crs_yields_warning() -> None:
    geojson = {
        "type": "Polygon",
        "coordinates": [
            [[51.0, 35.0], [51.1, 35.0], [51.1, 35.1], [51.0, 35.1], [51.0, 35.0]]
        ],
    }
    result = validate_geometry(geojson, "EPSG:4326")
    assert result.valid is True
    assert result.area_m2 is None
    assert any("geographic" in w.lower() for w in result.warnings)


def test_empty_geometry_is_invalid() -> None:
    geojson = {"type": "Polygon", "coordinates": []}
    result = validate_geometry(geojson, "EPSG:3857")
    assert result.valid is False

# --- Phase 1.2: building metric computations ---


def test_compute_metrics_without_building_returns_parcel_only() -> None:
    v = ValidationResult(valid=True, area_m2=100.0, perimeter_m=40.0, crs="EPSG:3857")
    metrics = compute_metrics(v)
    assert metrics == {
        "area_m2": 100.0,
        "perimeter_m": 40.0,
        "crs": "EPSG:3857",
    }


def test_compute_metrics_adds_height_and_setback() -> None:
    v = ValidationResult(valid=True, area_m2=200.0, perimeter_m=60.0)
    b = BuildingInputs(height_m=12.0, setback_m=3.5)
    metrics = compute_metrics(v, b)
    assert metrics["height_m"] == pytest.approx(12.0)
    assert metrics["setback_m"] == pytest.approx(3.5)
    assert "coverage_ratio" not in metrics
    assert "far_ratio" not in metrics


def test_compute_metrics_derives_coverage_ratio() -> None:
    v = ValidationResult(valid=True, area_m2=100.0)
    b = BuildingInputs(footprint_m2=40.0)
    metrics = compute_metrics(v, b)
    assert metrics["coverage_ratio"] == pytest.approx(0.4)
    assert "far_ratio" not in metrics


def test_compute_metrics_derives_far_when_floors_provided() -> None:
    v = ValidationResult(valid=True, area_m2=100.0)
    b = BuildingInputs(footprint_m2=40.0, floors=3)
    metrics = compute_metrics(v, b)
    assert metrics["coverage_ratio"] == pytest.approx(0.4)
    assert metrics["far_ratio"] == pytest.approx(1.2)


def test_compute_metrics_skips_ratios_when_area_missing() -> None:
    v = ValidationResult(valid=True, area_m2=None)
    b = BuildingInputs(footprint_m2=40.0, floors=2)
    metrics = compute_metrics(v, b)
    assert "coverage_ratio" not in metrics
    assert "far_ratio" not in metrics


def test_compute_metrics_skips_far_when_floors_missing() -> None:
    v = ValidationResult(valid=True, area_m2=100.0)
    b = BuildingInputs(footprint_m2=40.0)
    metrics = compute_metrics(v, b)
    assert "far_ratio" not in metrics


def test_compute_metrics_invalid_geometry_still_carries_building_fields() -> None:
    """Invalid geometry (no area) keeps height/setback but skips ratios."""
    v = ValidationResult(valid=False, reason="bad geometry")
    b = BuildingInputs(height_m=10.0, footprint_m2=40.0, floors=2)
    metrics = compute_metrics(v, b)
    assert metrics["area_m2"] is None
    assert metrics["height_m"] == pytest.approx(10.0)
    assert "coverage_ratio" not in metrics
    assert "far_ratio" not in metrics