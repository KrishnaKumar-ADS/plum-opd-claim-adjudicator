"""Appeal workflow APIs."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db
from backend.models.appeal import Appeal
from backend.models.claim import Claim
from backend.utils.constants import AppealStatus, ClaimStatus
from backend.utils.logger import get_logger

logger = get_logger("api.appeals")
router = APIRouter(prefix="/api/appeals", tags=["Appeals"])


class AppealCreate(BaseModel):
    claim_id: str
    reason: str
    supporting_info: Optional[str] = ""


class AppealReview(BaseModel):
    reviewer_notes: str
    new_decision: Optional[str] = None
    new_approved_amount: Optional[float] = None


@router.post("")
def create_appeal(data: AppealCreate, db: Session = Depends(get_db)):
    """Create a new appeal."""
    claim = db.query(Claim).filter(Claim.claim_id == data.claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    appeal = Appeal(
        appeal_id=f"APL_{uuid.uuid4().hex[:5].upper()}",
        claim_id=data.claim_id,
        reason=data.reason,
        supporting_info=data.supporting_info,
        status=AppealStatus.SUBMITTED.value,
    )
    db.add(appeal)
    claim.status = ClaimStatus.APPEALED.value
    db.commit()
    return appeal.to_dict()


@router.get("")
def list_appeals(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all appeals."""
    appeals = db.query(Appeal).order_by(Appeal.created_at.desc()).offset(skip).limit(limit).all()
    return {"appeals": [a.to_dict() for a in appeals], "total": db.query(Appeal).count()}


@router.get("/{appeal_id}")
def get_appeal(appeal_id: str, db: Session = Depends(get_db)):
    """Get appeal details."""
    appeal = db.query(Appeal).filter(Appeal.appeal_id == appeal_id).first()
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    return appeal.to_dict()


@router.put("/{appeal_id}/review")
def review_appeal(appeal_id: str, data: AppealReview, db: Session = Depends(get_db)):
    """Review and resolve an appeal."""
    appeal = db.query(Appeal).filter(Appeal.appeal_id == appeal_id).first()
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")

    appeal.status = AppealStatus.UNDER_REVIEW.value
    appeal.reviewer_notes = data.reviewer_notes
    appeal.reviewed_at = datetime.utcnow()

    if data.new_decision:
        appeal.new_decision = data.new_decision
        appeal.new_approved_amount = data.new_approved_amount
        appeal.status = AppealStatus.APPROVED.value if data.new_decision == "APPROVED" else AppealStatus.REJECTED.value

        # Update Claim status to CLOSED
        claim = db.query(Claim).filter(Claim.claim_id == appeal.claim_id).first()
        if claim:
            claim.status = ClaimStatus.CLOSED.value

        # Update the original Decision with the appeal resolution
        from backend.models.decision import Decision
        decision = db.query(Decision).filter(Decision.claim_id == appeal.claim_id).first()
        if decision:
            decision.decision = data.new_decision
            if data.new_approved_amount is not None:
                decision.approved_amount = data.new_approved_amount
            else:
                decision.approved_amount = 0.0
            decision.notes = f"Appeal resolved ({appeal.status}): {data.reviewer_notes}"

    db.commit()
    return appeal.to_dict()
