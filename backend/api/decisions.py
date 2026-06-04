"""Decision retrieval APIs."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.models.decision import Decision
from backend.utils.logger import get_logger

logger = get_logger("api.decisions")
router = APIRouter(prefix="/api/decisions", tags=["Decisions"])


@router.get("")
def list_decisions(
    decision_type: Optional[str] = Query(None),
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db),
):
    """List decisions with optional filtering."""
    query = db.query(Decision)
    if decision_type:
        query = query.filter(Decision.decision == decision_type.upper())
    decisions = query.order_by(Decision.created_at.desc()).offset(skip).limit(limit).all()
    total = query.count()
    return {"decisions": [d.to_dict() for d in decisions], "total": total}


@router.get("/{claim_id}")
def get_decision(claim_id: str, db: Session = Depends(get_db)):
    """Get decision for a specific claim."""
    decision = db.query(Decision).filter(Decision.claim_id == claim_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision.to_dict()
