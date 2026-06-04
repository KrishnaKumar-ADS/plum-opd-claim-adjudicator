"""Claim database model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from backend.database import Base


class Claim(Base):
    """Represents an OPD insurance claim submission."""

    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String(20), unique=True, nullable=False, index=True)
    member_id = Column(String(20), nullable=False, index=True)
    member_name = Column(String(200), nullable=False)
    member_join_date = Column(String(20), nullable=True)
    treatment_date = Column(String(20), nullable=False)
    claim_amount = Column(Float, nullable=False)
    hospital = Column(String(200), nullable=True)
    cashless_request = Column(Integer, default=0)  # 0=False, 1=True
    previous_claims_same_day = Column(Integer, default=0)

    # Document data (stored as JSON)
    documents = Column(JSON, nullable=True)
    uploaded_files = Column(JSON, nullable=True)  # file paths

    # Extracted data from AI processing
    extracted_data = Column(JSON, nullable=True)

    # Status tracking
    status = Column(String(20), default="SUBMITTED")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Claim {self.claim_id} - {self.member_name} - ₹{self.claim_amount}>"

    def to_dict(self):
        return {
            "id": self.id,
            "claim_id": self.claim_id,
            "member_id": self.member_id,
            "member_name": self.member_name,
            "member_join_date": self.member_join_date,
            "treatment_date": self.treatment_date,
            "claim_amount": self.claim_amount,
            "hospital": self.hospital,
            "cashless_request": bool(self.cashless_request),
            "previous_claims_same_day": self.previous_claims_same_day,
            "documents": self.documents,
            "extracted_data": self.extracted_data,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
