"""Decision database model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from backend.database import Base


class Decision(Base):
    """Represents an adjudication decision for a claim."""

    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String(20), ForeignKey("claims.claim_id"), nullable=False, index=True)

    # Decision outcome
    decision = Column(String(20), nullable=False)  # APPROVED/REJECTED/PARTIAL/MANUAL_REVIEW
    approved_amount = Column(Float, default=0.0)
    claimed_amount = Column(Float, default=0.0)

    # Detailed reasoning
    rejection_reasons = Column(JSON, nullable=True)  # List of rejection codes
    rejected_items = Column(JSON, nullable=True)  # Items not covered
    deductions = Column(JSON, nullable=True)  # Copay, network discount, etc.
    flags = Column(JSON, nullable=True)  # Fraud flags

    # Confidence
    confidence_score = Column(Float, default=0.0)

    # Notes and next steps
    notes = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)  # Full AI reasoning chain

    # Adjudication steps breakdown
    eligibility_result = Column(JSON, nullable=True)
    coverage_result = Column(JSON, nullable=True)
    limits_result = Column(JSON, nullable=True)
    medical_necessity_result = Column(JSON, nullable=True)
    fraud_result = Column(JSON, nullable=True)

    # Cashless
    cashless_approved = Column(Integer, default=0)
    network_discount = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Integer, default=0)

    def __repr__(self):
        return f"<Decision {self.claim_id} - {self.decision} - ₹{self.approved_amount}>"

    def to_dict(self):
        return {
            "id": self.id,
            "claim_id": self.claim_id,
            "decision": self.decision,
            "approved_amount": self.approved_amount,
            "claimed_amount": self.claimed_amount,
            "rejection_reasons": self.rejection_reasons or [],
            "rejected_items": self.rejected_items or [],
            "deductions": self.deductions or {},
            "flags": self.flags or [],
            "confidence_score": self.confidence_score,
            "notes": self.notes,
            "next_steps": self.next_steps,
            "reasoning": self.reasoning,
            "eligibility_result": self.eligibility_result,
            "coverage_result": self.coverage_result,
            "limits_result": self.limits_result,
            "medical_necessity_result": self.medical_necessity_result,
            "fraud_result": self.fraud_result,
            "cashless_approved": bool(self.cashless_approved),
            "network_discount": self.network_discount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processing_time_ms": self.processing_time_ms,
        }
