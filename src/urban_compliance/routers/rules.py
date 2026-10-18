"""CRUD endpoints for data-driven rules."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


@router.post("", response_model=schemas.RuleOut, status_code=201)
def create_rule(payload: schemas.RuleCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Rule).filter(models.Rule.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="rule with this code already exists")

    rule = models.Rule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("", response_model=list[schemas.RuleOut])
def list_rules(
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(models.Rule)
    if active_only:
        query = query.filter(models.Rule.is_active.is_(True))
    return query.order_by(models.Rule.id.asc()).all()


@router.get("/{rule_id}", response_model=schemas.RuleOut)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(models.Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    return rule


@router.patch("/{rule_id}/verify", response_model=schemas.RuleOut)
def verify_rule(rule_id: int, db: Session = Depends(get_db)):
    """Mark a rule as verified by a domain expert."""
    rule = db.get(models.Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    rule.is_verified = True
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}/deactivate", response_model=schemas.RuleOut)
def deactivate_rule(rule_id: int, db: Session = Depends(get_db)):
    """Deactivate a rule so it is no longer applied in analyses."""
    rule = db.get(models.Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    rule.is_active = False
    db.commit()
    db.refresh(rule)
    return rule