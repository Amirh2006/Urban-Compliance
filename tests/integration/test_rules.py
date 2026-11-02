"""Integration tests for rule CRUD and rule-aware analyses."""

from fastapi.testclient import TestClient

from urban_compliance.main import app

VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
    "crs": "EPSG:3857",
}


def _create_rule(client: TestClient, **overrides) -> dict:
    payload = {
        "code": "MIN_AREA_TEST",
        "title": "Minimum area test",
        "kind": "min_area",
        "threshold": 50.0,
        "is_verified": True,
    }
    payload.update(overrides)
    response = client.post("/api/v1/rules", json=payload)
    return response


def test_create_and_list_rules() -> None:
    with TestClient(app) as client:
        response = _create_rule(client)
        assert response.status_code == 201
        rule = response.json()
        assert rule["code"] == "MIN_AREA_TEST"
        assert rule["is_verified"] is True

        listing = client.get("/api/v1/rules")
        assert listing.status_code == 200
        codes = [r["code"] for r in listing.json()]
        assert "MIN_AREA_TEST" in codes


def test_duplicate_rule_code_returns_conflict() -> None:
    with TestClient(app) as client:
        _create_rule(client, code="DUP_RULE")
        second = _create_rule(client, code="DUP_RULE")
        assert second.status_code == 409


def test_verify_and_deactivate_rule() -> None:
    with TestClient(app) as client:
        created = _create_rule(client, code="TO_VERIFY", is_verified=False)
        rule_id = created.json()["id"]

        verified = client.patch(f"/api/v1/rules/{rule_id}/verify")
        assert verified.status_code == 200
        assert verified.json()["is_verified"] is True

        deactivated = client.patch(f"/api/v1/rules/{rule_id}/deactivate")
        assert deactivated.status_code == 200
        assert deactivated.json()["is_active"] is False


def test_analysis_evaluates_verified_rule() -> None:
    with TestClient(app) as client:
        _create_rule(client, code="MIN_AREA_RULE", threshold=50.0, is_verified=True)
        project = client.post("/api/v1/projects", json={"name": "Rules Project"})
        project_id = project.json()["id"]

        analysis = client.post(
            "/api/v1/analyses",
            json={"project_id": project_id, "geometry": VALID_POLYGON},
        )
        assert analysis.status_code == 201
        body = analysis.json()

        assert body["status"] == "verified"
        rule_results = body["result"]["rules"]
        assert any(r["rule_code"] == "MIN_AREA_RULE" for r in rule_results)
        assert all(r["status"] in ("verified", "not_applicable") for r in rule_results)


def test_analysis_fails_when_rule_violated() -> None:
    with TestClient(app) as client:
        _create_rule(client, code="MIN_AREA_BIG", threshold=1000.0, is_verified=True)
        project = client.post("/api/v1/projects", json={"name": "Violation Project"})
        project_id = project.json()["id"]

        analysis = client.post(
            "/api/v1/analyses",
            json={"project_id": project_id, "geometry": VALID_POLYGON},
        )
        body = analysis.json()
        assert body["status"] == "failed"
        statuses = [r["status"] for r in body["result"]["rules"]]
        assert "failed" in statuses


def test_analysis_marks_needs_review_for_unverified_rule() -> None:
    with TestClient(app) as client:
        _create_rule(
            client, code="MIN_AREA_UNVERIFIED", threshold=50.0, is_verified=False
        )
        project = client.post("/api/v1/projects", json={"name": "Unverified Project"})
        project_id = project.json()["id"]

        analysis = client.post(
            "/api/v1/analyses",
            json={"project_id": project_id, "geometry": VALID_POLYGON},
        )
        body = analysis.json()
        assert body["status"] == "needs_review"


def test_report_includes_rule_results() -> None:
    with TestClient(app) as client:
        _create_rule(client, code="MIN_AREA_REPORT", threshold=50.0, is_verified=True)
        project = client.post("/api/v1/projects", json={"name": "Report Rule Project"})
        project_id = project.json()["id"]
        analysis = client.post(
            "/api/v1/analyses",
            json={"project_id": project_id, "geometry": VALID_POLYGON},
        )
        analysis_id = analysis.json()["id"]

        report = client.get(f"/api/v1/analyses/{analysis_id}/report")
        assert report.status_code == 200
        body = report.json()
        assert body["rules_applied"]
        assert any(r["rule_code"] == "MIN_AREA_REPORT" for r in body["rules_applied"])

# --- Phase 1.3: spatial scope filtering ---


def _create_scoped_project(client: TestClient, *, scope: str | None, name: str) -> int:
    """Create a project with an optional spatial scope and return its id."""
    payload: dict = {"name": name}
    if scope is not None:
        payload["spatial_scope"] = scope
    response = client.post("/api/v1/projects", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


def test_project_persists_spatial_scope() -> None:
    with TestClient(app) as client:
        project_id = _create_scoped_project(client, scope="district_3", name="Scoped")
        fetched = client.get(f"/api/v1/projects/{project_id}")
        assert fetched.status_code == 200
        assert fetched.json()["spatial_scope"] == "district_3"


def test_project_without_spatial_scope_serialises_as_null() -> None:
    with TestClient(app) as client:
        project_id = _create_scoped_project(client, scope=None, name="Unscoped")
        fetched = client.get(f"/api/v1/projects/{project_id}")
        assert fetched.json()["spatial_scope"] is None


def test_scoped_rule_applies_when_project_scope_matches() -> None:
    with TestClient(app) as client:
        _create_rule(
            client,
            code="MIN_AREA_D3",
            threshold=50.0,
            is_verified=True,
            spatial_scope="district_3",
        )
        project_id = _create_scoped_project(client, scope="district_3", name="Match")

        analysis = client.post(
            "/api/v1/analyses",
            json={"project_id": project_id, "geometry": VALID_POLYGON},
        )
        body = analysis.json()
        assert analysis.status_code == 201
        rule_codes = [r["rule_code"] for r in body["result"]["rules"]]
        assert "MIN_AREA_D3" in rule_codes


def test_scoped_rule_is_skipped_when_project_scope_differs() -> None:
    with TestClient(app) as client:
        _create_rule(
            client,
            code="MIN_AREA_D5",
            threshold=1000.0,  # would fail if evaluated
            is_verified=True,
            spatial_scope="district_5",
        )
        project_id = _create_scoped_project(client, scope="district_3", name="Mismatch")

        analysis = client.post(
            "/api/v1/analyses",
            json={"project_id": project_id, "geometry": VALID_POLYGON},
        )
        body = analysis.json()
        # Rule was filtered out, so the analysis cannot fail because of it.
        assert analysis.status_code == 201
        rule_codes = [r["rule_code"] for r in body["result"]["rules"]]
        assert "MIN_AREA_D5" not in rule_codes


def test_global_rule_applies_to_scoped_project() -> None:
    with TestClient(app) as client:
        _create_rule(
            client,
            code="MIN_AREA_GLOBAL",
            threshold=50.0,
            is_verified=True,
            spatial_scope=None,
        )
        project_id = _create_scoped_project(client, scope="district_3", name="Global")

        analysis = client.post(
            "/api/v1/analyses",
            json={"project_id": project_id, "geometry": VALID_POLYGON},
        )
        body = analysis.json()
        rule_codes = [r["rule_code"] for r in body["result"]["rules"]]
        assert "MIN_AREA_GLOBAL" in rule_codes


def test_unscoped_project_evaluates_every_rule() -> None:
    with TestClient(app) as client:
        _create_rule(
            client, code="MIN_AREA_ANY_GLOBAL",
            threshold=50.0, is_verified=True, spatial_scope=None,
        )
        _create_rule(
            client, code="MIN_AREA_ANY_D7",
            threshold=50.0, is_verified=True, spatial_scope="district_7",
        )
        project_id = _create_scoped_project(client, scope=None, name="NoScope")

        analysis = client.post(
            "/api/v1/analyses",
            json={"project_id": project_id, "geometry": VALID_POLYGON},
        )
        body = analysis.json()
        rule_codes = [r["rule_code"] for r in body["result"]["rules"]]
        # Per spec: no project scope means every rule is evaluated.
        assert "MIN_AREA_ANY_GLOBAL" in rule_codes
        assert "MIN_AREA_ANY_D7" in rule_codes