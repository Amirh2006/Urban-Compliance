"""Unit tests for the geometry validation engine."""

import pytest

from urban_compliance.geometry.engine import validate_geometry


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