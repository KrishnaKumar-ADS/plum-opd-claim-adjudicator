"""Appeal review workflow."""

import uuid
from datetime import datetime
from backend.services.adjudication_service import adjudicate_claim
from backend.utils.constants import AppealStatus
from backend.utils.logger import get_logger

logger = get_logger("appeal_service")


def create_appeal(claim_id: str, reason: str, supporting_info: str = "") -> dict:
    """Create a new appeal for a rejected/partial claim."""
    appeal_id = f"APL_{uuid.uuid4().hex[:5].upper()}"
    return {
        "appeal_id": appeal_id,
        "claim_id": claim_id,
        "reason": reason,
        "supporting_info": supporting_info,
        "status": AppealStatus.SUBMITTED.value,
        "created_at": datetime.utcnow().isoformat(),
    }


def review_appeal(appeal_data: dict, claim_data: dict, reviewer_notes: str, new_decision: str = None) -> dict:
    """Review an appeal — can override or re-adjudicate."""
    appeal_data["status"] = AppealStatus.UNDER_REVIEW.value
    appeal_data["reviewer_notes"] = reviewer_notes
    appeal_data["reviewed_at"] = datetime.utcnow().isoformat()

    if new_decision:
        appeal_data["new_decision"] = new_decision
        appeal_data["status"] = AppealStatus.APPROVED.value if new_decision == "APPROVED" else AppealStatus.REJECTED.value
    else:
        # Re-adjudicate with appeal context
        claim_data["appeal_context"] = appeal_data.get("reason", "")
        result = adjudicate_claim(claim_data)
        appeal_data["new_decision"] = result.get("decision", "REJECTED")
        appeal_data["new_approved_amount"] = result.get("approved_amount", 0)
        appeal_data["status"] = AppealStatus.APPROVED.value if result.get("decision") == "APPROVED" else AppealStatus.REJECTED.value

    logger.info(f"Appeal {appeal_data['appeal_id']} reviewed: {appeal_data['status']}")
    return appeal_data
