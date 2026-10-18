"""Pure evaluation logic for data-driven rules.

This module contains no database access and no HTTP concerns. It takes a
rule definition and the metrics computed for a parcel, and returns a
deterministic outcome. Rules that cannot be evaluated produce
``needs_review`` instead of fabricating a verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Supported rule kinds in this MVP. Adding a new kind means adding a new
# entry here and a corresponding branch in ``evaluate_rule``.
SUPPORTED_KINDS = ("min_area", "max_area", "min_perimeter")

VALID_OUTCOMES = ("verified", "failed", "needs_review", "not_applicable")


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
    if kind in ("min_area", "max_area"):
        return metrics.get("area_m2")
    if kind == "min_perimeter":
        return metrics.get("perimeter_m")
    return None


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

    if kind == "min_area":
        passes = actual_value >= threshold
    elif kind == "max_area":
        passes = actual_value <= threshold
    elif kind == "min_perimeter":
        passes = actual_value >= threshold
    else:  # pragma: no cover - guarded by SUPPORTED_KINDS
        passes = False

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