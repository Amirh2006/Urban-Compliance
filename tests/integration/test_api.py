"""Integration tests covering the main API flows."""

from fastapi.testclient import TestClient

from urban_compliance.main import app

VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
    "crs": "EPSG:3857",
}


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_fetch_project() -> None:
    with TestClient(app) as client:
        created = client.post("/api/v1/projects", json={"name": "Test Project"})
        assert created.status_code == 201
        project_id = created.json()["id"]

        fetched = client.get(f"/api/v1/projects/{project_id}")
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "Test Project"


def test_unknown_project_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/projects/999999")
    assert response.status_code == 404


def test_parcels_validate_returns_area_for_projected_crs() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/parcels/validate", json=VALID_POLYGON)
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["area_m2"] == 100.0
    assert body["perimeter_m"] == 40.0


def test_parcels_validate_missing_crs_yields_warning() -> None:
    payload = dict(VALID_POLYGON)
    payload.pop("crs")
    with TestClient(app) as client:
        response = client.post("/api/v1/parcels/validate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["area_m2"] is None
    assert body["warnings"]


def test_create_analysis_with_geometry_and_no_rules_yields_partial() -> None:
    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Analysis Project"})
        project_id = project.json()["id"]

        response = client.post(
            "/api/v1/analyses",
            json={"project_id": project_id, "geometry": VALID_POLYGON},
        )
    assert response.status_code == 201
    body = response.json()
    # No rules are configured, so only geometry was checked: partial coverage.
    assert body["status"] == "partial"
    assert body["result"]["tests"][0]["status"] == "verified"
    assert body["result"]["rules"] == []

def test_create_analysis_without_input_marks_failed() -> None:
    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Bad Project"})
        project_id = project.json()["id"]

        response = client.post("/api/v1/analyses", json={"project_id": project_id})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert body["result"]["error"]


def test_upload_and_process_geojson(tmp_path) -> None:
    import json

    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]]],
                },
                "properties": {},
            }
        ],
    }
    file_path = tmp_path / "sample.geojson"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Upload Project"})
        project_id = project.json()["id"]

        with file_path.open("rb") as fh:
            upload = client.post(
                f"/api/v1/projects/{project_id}/files",
                files={"file": ("sample.geojson", fh, "application/geo+json")},
            )
        assert upload.status_code == 201
        file_id = upload.json()["id"]

        processed = client.post(f"/api/v1/files/{file_id}/process")
        assert processed.status_code == 200
        assert processed.json()["status"] == "parsed"