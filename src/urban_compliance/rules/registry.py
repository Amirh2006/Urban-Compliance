"""Load active rules from the database and evaluate them for a parcel."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .. import models
from .evaluator import RuleEvaluation, evaluate_rule


def load_active_rules(db: Session) -> list[models.Rule]:
    """Return all active rules in a stable order."""
    return (
        db.query(models.Rule)
        .filter(models.Rule.is_active.is_(True))
        .order_by(models.Rule.id.asc())
        .all()
    )


def _scope_matches(rule_scope: str | None, parcel_scope: str | None) -> bool:
    """Return True when a rule with ``rule_scope`` applies to ``parcel_scope``.

    - A rule without a scope is global and always applies.
    - When the parcel does not declare a scope, every rule is evaluated so
      that the user sees all candidate rules, not a silent subset.
    - Otherwise, the rule applies only when both scopes are exactly equal.
    """
    if rule_scope is None:
        return True
    if parcel_scope is None:
        return True
    return rule_scope == parcel_scope


def evaluate_all(
    db: Session,
    metrics: dict[str, Any],
    *,
    spatial_scope: str | None = None,
) -> list[RuleEvaluation]:
    """Evaluate every applicable active rule and return a list of evaluations.

    ``spatial_scope`` is the parcel's scope. Rules whose scope does not match
    are skipped before evaluation, so their outcome is never reported.
    """
    results: list[RuleEvaluation] = []
    for rule in load_active_rules(db):
        if not _scope_matches(rule.spatial_scope, spatial_scope):
            continue
        results.append(
            evaluate_rule(
                rule_id=rule.id,
                rule_code=rule.code,
                kind=rule.kind,
                threshold=rule.threshold,
                metrics=metrics,
                is_active=rule.is_active,
                is_verified=rule.is_verified,
                source_reference=rule.source_reference,
            )
        )
    return results