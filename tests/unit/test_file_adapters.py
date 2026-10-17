"""Unit tests for the file adapters."""

import json
from pathlib import Path

from urban_compliance.file_adapters.csv_adapter import CSVAdapter
from urban_compliance.file_adapters.geojson_adapter import GeoJSONAdapter
from urban_compliance.file_adapters.registry import get_adapter, parse_file


def test_geojson_adapter_reads_feature_collection(tmp_path: Path) -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
                "properties": {},
            }
        ],
    }
    path = tmp_path / "parcel.geojson"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = GeoJSONAdapter().parse(path)
    assert result.ok is True
    assert result.geojson is not None
    assert result.geojson["type"] == "Polygon"


def test_geojson_adapter_reports_empty_feature_collection(tmp_path: Path) -> None:
    path = tmp_path / "empty.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": []}), encoding="utf-8")

    result = GeoJSONAdapter().parse(path)
    assert result.ok is False
    assert result.error is not None


def test_geojson_adapter_handles_broken_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.geojson"
    path.write_text("{not json", encoding="utf-8")

    result = GeoJSONAdapter().parse(path)
    assert result.ok is False


def test_csv_adapter_builds_closed_polygon(tmp_path: Path) -> None:
    path = tmp_path / "points.csv"
    path.write_text("x,y\n0,0\n10,0\n10,10\n0,10\n", encoding="utf-8")

    result = CSVAdapter().parse(path)
    assert result.ok is True
    assert result.geojson is not None
    ring = result.geojson["coordinates"][0]
    assert ring[0] == ring[-1]
    assert len(ring) == 5


def test_csv_adapter_rejects_missing_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

    result = CSVAdapter().parse(path)
    assert result.ok is False


def test_csv_adapter_rejects_too_few_points(tmp_path: Path) -> None:
    path = tmp_path / "few.csv"
    path.write_text("x,y\n0,0\n1,1\n", encoding="utf-8")

    result = CSVAdapter().parse(path)
    assert result.ok is False


def test_registry_selects_adapter_by_extension(tmp_path: Path) -> None:
    assert get_adapter(tmp_path / "a.geojson") is not None
    assert get_adapter(tmp_path / "a.csv") is not None
    assert get_adapter(tmp_path / "a.dxf") is None


def test_registry_returns_error_for_unsupported_extension(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"
    path.write_text("hello", encoding="utf-8")

    result = parse_file(path)
    assert result.ok is False
    assert "unsupported" in (result.error or "")