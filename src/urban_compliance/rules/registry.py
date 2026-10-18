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


def evaluate_all(
    db: Session,
    metrics: dict[str, Any],
    *,
    spatial_scope: str | None = None,
) -> list[RuleEvaluation]:
    """Evaluate every active rule and return a list of evaluations.

    ``spatial_scope`` is currently informational only. It is stored on the
    rule for traceability but does not filter evaluation in this MVP.
    """
    results: list[RuleEvaluation] = []
    for rule in load_active_rules(db):
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