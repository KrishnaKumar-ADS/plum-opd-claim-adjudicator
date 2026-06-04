"""Appeal workflow model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from backend.database import Base


class Appeal(Base):
    """Represents an appeal against an adjudication decision."""

    __tablename__ = "appeals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appeal_id = Column(String(20), unique=True, nullable=False, index=True)
    claim_id = Column(String(20), ForeignKey("claims.claim_id"), nullable=False, index=True)

    # Appeal details
    reason = Column(Text, nullable=False)
    supporting_info = Column(Text, nullable=True)
    additional_documents = Column(JSON, nullable=True)

    # Review
    status = Column(String(20), default="SUBMITTED")
    reviewer_notes = Column(Text, nullable=True)
    new_decision = Column(String(20), nullable=True)
    new_approved_amount = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Appeal {self.appeal_id} for {self.claim_id} - {self.status}>"

    def to_dict(self):
        return {
            "id": self.id,
            "appeal_id": self.appeal_id,
            "claim_id": self.claim_id,
            "reason": self.reason,
            "supporting_info": self.supporting_info,
            "additional_documents": self.additional_documents,
            "status": self.status,
            "reviewer_notes": self.reviewer_notes,
            "new_decision": self.new_decision,
            "new_approved_amount": self.new_approved_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
