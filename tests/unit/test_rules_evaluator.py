"""Unit tests for the pure rule evaluator."""

from urban_compliance.rules.evaluator import evaluate_rule


def test_min_area_passes_when_metric_meets_threshold() -> None:
    result = evaluate_rule(
        rule_id=1,
        rule_code="MIN_AREA_100",
        kind="min_area",
        threshold=100.0,
        metrics={"area_m2": 150.0, "perimeter_m": 40.0},
    )
    assert result.status == "verified"
    assert result.actual == 150.0
    assert result.threshold == 100.0


def test_min_area_fails_when_metric_below_threshold() -> None:
    result = evaluate_rule(
        rule_id=2,
        rule_code="MIN_AREA_100",
        kind="min_area",
        threshold=100.0,
        metrics={"area_m2": 80.0, "perimeter_m": 40.0},
    )
    assert result.status == "failed"


def test_max_area_fails_when_metric_above_threshold() -> None:
    result = evaluate_rule(
        rule_id=3,
        rule_code="MAX_AREA_500",
        kind="max_area",
        threshold=500.0,
        metrics={"area_m2": 800.0, "perimeter_m": 40.0},
    )
    assert result.status == "failed"


def test_min_perimeter_uses_perimeter_metric() -> None:
    result = evaluate_rule(
        rule_id=4,
        rule_code="MIN_PERIM_10",
        kind="min_perimeter",
        threshold=10.0,
        metrics={"area_m2": 100.0, "perimeter_m": 12.0},
    )
    assert result.status == "verified"


def test_missing_metric_yields_needs_review() -> None:
    result = evaluate_rule(
        rule_id=5,
        rule_code="MIN_AREA_100",
        kind="min_area",
        threshold=100.0,
        metrics={"area_m2": None, "perimeter_m": None},
    )
    assert result.status == "needs_review"
    assert result.actual is None


def test_unverified_rule_is_flagged() -> None:
    result = evaluate_rule(
        rule_id=6,
        rule_code="MIN_AREA_100",
        kind="min_area",
        threshold=100.0,
        metrics={"area_m2": 500.0},
        is_verified=False,
    )
    assert result.status == "needs_review"


def test_inactive_rule_is_not_applicable() -> None:
    result = evaluate_rule(
        rule_id=7,
        rule_code="MIN_AREA_100",
        kind="min_area",
        threshold=100.0,
        metrics={"area_m2": 500.0},
        is_active=False,
    )
    assert result.status == "not_applicable"


def test_unsupported_kind_yields_needs_review() -> None:
    result = evaluate_rule(
        rule_id=8,
        rule_code="WEIRD",
        kind="magic",
        threshold=1.0,
        metrics={"area_m2": 1.0},
    )
    assert result.status == "needs_review"