"""Integration tests for the JSON report endpoint."""

from fastapi.testclient import TestClient

from urban_compliance.main import app

VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
    "crs": "EPSG:3857",
}


def _create_project_and_analysis(client: TestClient, geometry: dict | None) -> int:
    project = client.post("/api/v1/projects", json={"name": "Report Project"})
    assert project.status_code == 201
    project_id = project.json()["id"]

    body: dict = {"project_id": project_id}
    if geometry is not None:
        body["geometry"] = geometry

    analysis = client.post("/api/v1/analyses", json=body)
    assert analysis.status_code == 201
    return analysis.json()["id"]


def test_report_for_verified_analysis() -> None:
    with TestClient(app) as client:
        analysis_id = _create_project_and_analysis(client, VALID_POLYGON)
        response = client.get(f"/api/v1/analyses/{analysis_id}/report")

    assert response.status_code == 200
    report = response.json()

    assert report["report_id"] == f"RPT-{analysis_id:06d}"
    assert report["report_version"] == "0.1.0"
    assert report["generated_at"]
    assert "not constitute an official approval" in report["disclaimer"]

    assert report["project"]["name"] == "Report Project"
    assert report["analysis"]["status"] == "verified"

    summary = report["summary"]
    assert summary["overall_status"] == "verified"
    assert summary["test_count"] == 1
    assert summary["verified_count"] == 1
    assert summary["failed_count"] == 0

    assert len(report["tests"]) == 1
    assert report["tests"][0]["name"] == "geometry_validity"
    assert report["tests"][0]["area_m2"] == 100.0

    assert report["input_error"] is None
    assert report["rules_applied"] == []
    assert report["sources"] == []
    assert isinstance(report["limitations"], list) and report["limitations"]
    assert isinstance(report["assumptions"], list) and report["assumptions"]


def test_report_for_failed_analysis_lists_review_items() -> None:
    with TestClient(app) as client:
        analysis_id = _create_project_and_analysis(client, None)
        response = client.get(f"/api/v1/analyses/{analysis_id}/report")

    assert response.status_code == 200
    report = response.json()

    assert report["analysis"]["status"] == "failed"
    assert report["summary"]["overall_status"] == "failed"
    assert report["input_error"] == "geometry or file_id is required"


def test_report_for_missing_analysis_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/analyses/999999/report")
    assert response.status_code == 404


def test_report_includes_warnings_from_missing_crs() -> None:
    payload = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    }
    with TestClient(app) as client:
        analysis_id = _create_project_and_analysis(client, payload)
        response = client.get(f"/api/v1/analyses/{analysis_id}/report")

    assert response.status_code == 200
    report = response.json()
    assert report["analysis"]["status"] == "verified"
    assert any("CRS" in w for w in report["warnings"])