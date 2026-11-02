"""Unit tests for the pure rule evaluator."""
import pytest
from urban_compliance.rules.evaluator import (
    SUPPORTED_KINDS, RuleEvaluation, evaluate_rule,
)
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

# --- Phase 1.1: new rule kinds ---


@pytest.mark.parametrize(
    "kind, metric_key, actual, threshold, expected_status",
    [
        # max_height: lower is better
        ("max_height", "height_m", 20.0, 25.0, "verified"),
        ("max_height", "height_m", 30.0, 25.0, "failed"),
        # min_setback: higher is better
        ("min_setback", "setback_m", 3.5, 3.0, "verified"),
        ("min_setback", "setback_m", 2.0, 3.0, "failed"),
        # max_coverage: lower is better
        ("max_coverage", "coverage_ratio", 0.5, 0.6, "verified"),
        ("max_coverage", "coverage_ratio", 0.75, 0.6, "failed"),
        # far: lower is better
        ("far", "far_ratio", 2.0, 2.5, "verified"),
        ("far", "far_ratio", 3.0, 2.5, "failed"),
    ],
)
def test_evaluate_new_kinds(kind, metric_key, actual, threshold, expected_status):
    """Each new kind compares the correct metric in the correct direction."""
    result = evaluate_rule(
        rule_id=1,
        rule_code=f"TEST_{kind.upper()}",
        kind=kind,
        threshold=threshold,
        metrics={metric_key: actual},
        is_active=True,
        is_verified=True,
    )
    assert isinstance(result, RuleEvaluation)
    assert result.status == expected_status
    assert result.actual == actual
    assert result.threshold == threshold
    assert result.kind == kind


@pytest.mark.parametrize(
    "kind", ["max_height", "min_setback", "max_coverage", "far"]
)
def test_evaluate_new_kinds_missing_metric(kind):
    """New kinds yield needs_review when their metric is missing."""
    result = evaluate_rule(
        rule_id=1,
        rule_code=f"TEST_{kind.upper()}",
        kind=kind,
        threshold=1.0,
        metrics={},  # no metrics available
        is_active=True,
        is_verified=True,
    )
    assert result.status == "needs_review"
    assert result.actual is None
    assert result.warnings == ["metric missing; cannot evaluate rule"]


def test_supported_kinds_includes_phase_1_1_kinds():
    """The four new kinds are registered as supported."""
    for kind in ("max_height", "min_setback", "max_coverage", "far"):
        assert kind in SUPPORTED_KINDS