"""Smoke tests for the health endpoint."""

from fastapi.testclient import TestClient

from urban_compliance.main import app


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body