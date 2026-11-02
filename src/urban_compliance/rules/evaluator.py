"""Pure evaluation logic for data-driven rules.

This module contains no database access and no HTTP concerns. It takes a
rule definition and the metrics computed for a parcel, and returns a
deterministic outcome. Rules that cannot be evaluated produce
``needs_review`` instead of fabricating a verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Supported rule kinds. Each kind maps to a single metric in ``_METRIC_BY_KIND``
# and is compared against its threshold using the direction declared in
# ``_LOWER_BOUND_KINDS`` / ``_UPPER_BOUND_KINDS``. Adding a new kind means
# extending all three tables.
SUPPORTED_KINDS = (
    "min_area",
    "max_area",
    "min_perimeter",
    "max_height",
    "min_setback",
    "max_coverage",
    "far",
)

VALID_OUTCOMES = ("verified", "failed", "needs_review", "not_applicable")

# Maps each rule kind to the metric key it consumes from ``metrics``.
# Coverage and FAR are ratios in the 0..1 range; lengths are in meters;
# areas are in square meters.
_METRIC_BY_KIND: dict[str, str] = {
    "min_area": "area_m2",
    "max_area": "area_m2",
    "min_perimeter": "perimeter_m",
    "max_height": "height_m",
    "min_setback": "setback_m",
    "max_coverage": "coverage_ratio",
    "far": "far_ratio",
}

# Kinds where a higher actual value is better: pass when actual >= threshold.
_LOWER_BOUND_KINDS = frozenset({"min_area", "min_perimeter", "min_setback"})

# Kinds where a lower actual value is better: pass when actual <= threshold.
_UPPER_BOUND_KINDS = frozenset({"max_area", "max_height", "max_coverage", "far"})


@dataclass
class RuleEvaluation:
    """Result of applying a single rule to a parcel."""

    rule_id: int | None
    rule_code: str
    kind: str
    status: str
    message: str
    threshold: float | None = None
    actual: float | None = None
    source_reference: str | None = None
    warnings: list[str] = field(default_factory=list)


def _metric_for_kind(kind: str, metrics: dict[str, Any]) -> float | None:
    """Return the metric needed by a rule kind, or None if unavailable."""
    metric_name = _METRIC_BY_KIND.get(kind)
    if metric_name is None:
        return None
    return metrics.get(metric_name)


def _passes(kind: str, actual: float, threshold: float) -> bool:
    """Compare actual against threshold according to the rule's direction."""
    if kind in _LOWER_BOUND_KINDS:
        return actual >= threshold
    if kind in _UPPER_BOUND_KINDS:
        return actual <= threshold
    return False  # pragma: no cover - guarded by SUPPORTED_KINDS


def evaluate_rule(
    *,
    rule_id: int | None,
    rule_code: str,
    kind: str,
    threshold: float,
    metrics: dict[str, Any],
    is_active: bool = True,
    is_verified: bool = True,
    source_reference: str | None = None,
) -> RuleEvaluation:
    """Evaluate a single rule against computed metrics.

    The function never raises for missing data; instead it returns a
    ``needs_review`` evaluation with an explanatory message.
    """
    base = dict(
        rule_id=rule_id,
        rule_code=rule_code,
        kind=kind,
        threshold=float(threshold),
        source_reference=source_reference,
    )

    if not is_active:
        return RuleEvaluation(
            **base,
            status="not_applicable",
            message="rule is inactive",
        )

    if not is_verified:
        return RuleEvaluation(
            **base,
            status="needs_review",
            message="rule has not been verified by a domain expert",
            warnings=["expert verification is pending"],
        )

    if kind not in SUPPORTED_KINDS:
        return RuleEvaluation(
            **base,
            status="needs_review",
            message=f"unsupported rule kind: {kind}",
        )

    actual = _metric_for_kind(kind, metrics)
    if actual is None:
        return RuleEvaluation(
            **base,
            actual=None,
            status="needs_review",
            message="required metric is not available for this parcel",
            warnings=["metric missing; cannot evaluate rule"],
        )

    actual_value = float(actual)
    passes = _passes(kind, actual_value, threshold)

    return RuleEvaluation(
        **base,
        actual=actual_value,
        status="verified" if passes else "failed",
        message=(
            f"{kind} satisfied: actual={actual_value} threshold={threshold}"
            if passes
            else f"{kind} violated: actual={actual_value} threshold={threshold}"
        ),
    )