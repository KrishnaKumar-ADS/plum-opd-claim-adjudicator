"""Admin dashboard APIs."""

import json
import os
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models.claim import Claim
from backend.models.decision import Decision
from backend.models.appeal import Appeal
from backend.config import get_settings, get_policy_config
from backend.utils.logger import get_logger

logger = get_logger("api.admin")
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Default policy configuration (used if config file doesn't exist)
DEFAULT_POLICY_CONFIG = {
    "per_claim_limit": 5000,
    "annual_limit": 50000,
    "copay_percentage": 20,
    "confidence_threshold_manual": 0.70,
    "fraud_risk_threshold": 0.6,
    "max_medicines_per_claim": 10,
    "consultation_fee_limit": 1500,
    "diagnostic_tests_limit": 3000,
    "specialist_fee_limit": 2500,
    "network_discount_percentage": 10,
    "waiting_period_days": 30,
    "cashless_claim_limit": 10000,
}


def _get_policy_config_path() -> Path:
    settings = get_settings()
    return Path(settings.data_dir) / "config" / "policy_config.json"


def _load_policy_config() -> dict:
    """Load policy configuration from file, or return defaults."""
    return get_policy_config()


def _save_policy_config(config: dict) -> None:
    """Persist policy configuration to disk."""
    config_path = _get_policy_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get overview statistics for the admin dashboard."""
    total_claims = db.query(Claim).count()
    total_decisions = db.query(Decision).count()

    approved = db.query(Decision).filter(Decision.decision == "APPROVED").count()
    rejected = db.query(Decision).filter(Decision.decision == "REJECTED").count()
    partial = db.query(Decision).filter(Decision.decision == "PARTIAL").count()
    manual = db.query(Decision).filter(Decision.decision == "MANUAL_REVIEW").count()

    total_claimed = db.query(func.sum(Decision.claimed_amount)).scalar() or 0
    total_approved_amt = db.query(func.sum(Decision.approved_amount)).scalar() or 0
    avg_confidence = db.query(func.avg(Decision.confidence_score)).scalar() or 0
    avg_processing = db.query(func.avg(Decision.processing_time_ms)).scalar() or 0

    pending_appeals = db.query(Appeal).filter(Appeal.status == "SUBMITTED").count()

    return {
        "total_claims": total_claims,
        "decisions": {
            "approved": approved, "rejected": rejected,
            "partial": partial, "manual_review": manual,
        },
        "financials": {
            "total_claimed": round(total_claimed, 2),
            "total_approved": round(total_approved_amt, 2),
            "savings": round(total_claimed - total_approved_amt, 2),
        },
        "performance": {
            "avg_confidence": round(avg_confidence, 3),
            "avg_processing_ms": round(avg_processing, 0),
        },
        "pending_appeals": pending_appeals,
    }


@router.get("/review-queue")
def get_review_queue(db: Session = Depends(get_db)):
    """Get claims that need manual review (either MANUAL_REVIEW or under appeal)."""
    # 1. Standard manual reviews
    manual_decisions = db.query(Decision).filter(Decision.decision == "MANUAL_REVIEW").all()
    queue = []
    for d in manual_decisions:
        claim = db.query(Claim).filter(Claim.claim_id == d.claim_id).first()
        queue.append({
            "claim": claim.to_dict() if claim else {},
            "decision": d.to_dict(),
            "type": "manual_review",
        })

    # 2. Claims under active appeal
    pending_appeals = db.query(Appeal).filter(Appeal.status.in_(["SUBMITTED", "UNDER_REVIEW"])).all()
    for a in pending_appeals:
        claim = db.query(Claim).filter(Claim.claim_id == a.claim_id).first()
        decision = db.query(Decision).filter(Decision.claim_id == a.claim_id).first()
        queue.append({
            "claim": claim.to_dict() if claim else {},
            "decision": decision.to_dict() if decision else {},
            "type": "appeal",
            "appeal_id": a.appeal_id,
            "appeal_reason": a.reason,
            "appeal_supporting_info": a.supporting_info,
        })

    return {"queue": queue, "total": len(queue)}


@router.put("/review/{claim_id}")
def manual_review_decision(claim_id: str, body: dict, db: Session = Depends(get_db)):
    """Submit a manual review decision (handles both standard reviews and appeals)."""
    decision = db.query(Decision).filter(Decision.claim_id == claim_id).first()
    if not decision:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Decision not found")

    decision.decision = body.get("decision", decision.decision)
    decision.approved_amount = body.get("approved_amount", decision.approved_amount)
    decision.notes = body.get("notes", decision.notes)

    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    
    # Check if there is an active appeal for this claim
    appeal = db.query(Appeal).filter(Appeal.claim_id == claim_id, Appeal.status.in_(["SUBMITTED", "UNDER_REVIEW"])).first()
    if appeal:
        appeal.reviewer_notes = body.get("notes", "")
        appeal.new_decision = body.get("decision", decision.decision)
        appeal.new_approved_amount = body.get("approved_amount", decision.approved_amount)
        appeal.status = "APPROVED" if body.get("decision") == "APPROVED" else "REJECTED"
        appeal.reviewed_at = datetime.utcnow()
        if claim:
            claim.status = "CLOSED"  # Set claim status to CLOSED for resolved appeals
    else:
        if claim:
            claim.status = "ADJUDICATED"  # Regular manual review resolved

    db.commit()
    return decision.to_dict()


@router.get("/policy")
def get_policy_config():
    """Get current policy configuration (limits, thresholds)."""
    return _load_policy_config()


@router.put("/policy")
def update_policy_config(body: dict):
    """Update policy configuration. Merges with existing config."""
    current = _load_policy_config()

    # Validate numeric fields are non-negative
    numeric_fields = [
        "per_claim_limit", "annual_limit", "copay_percentage",
        "confidence_threshold_manual", "fraud_risk_threshold",
        "max_medicines_per_claim", "consultation_fee_limit",
        "diagnostic_tests_limit", "specialist_fee_limit",
        "network_discount_percentage", "waiting_period_days",
        "cashless_claim_limit",
    ]
    for field in numeric_fields:
        if field in body:
            val = body[field]
            if not isinstance(val, (int, float)) or val < 0:
                raise HTTPException(status_code=422, detail=f"Field '{field}' must be a non-negative number")

    current.update({k: v for k, v in body.items() if k in DEFAULT_POLICY_CONFIG})
    _save_policy_config(current)
    logger.info(f"Policy configuration updated: {list(body.keys())}")
    return current


@router.get("/policy/history")
def get_policy_history():
    """Return last-saved config with defaults for fields not yet saved."""
    return {
        "current": _load_policy_config(),
        "defaults": DEFAULT_POLICY_CONFIG,
    }
