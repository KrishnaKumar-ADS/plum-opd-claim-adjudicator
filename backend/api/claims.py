"""Claim submission APIs."""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.models.claim import Claim
from backend.models.decision import Decision
from backend.services.adjudication_service import adjudicate_claim
from backend.utils.constants import ClaimStatus
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("api.claims")
router = APIRouter(prefix="/api/claims", tags=["Claims"])
settings = get_settings()


MOCK_MEMBERS = {
    "rajesh kumar": {"id": "EMP001", "join_date": "2024-01-01"},
    "priya singh": {"id": "EMP002", "join_date": "2024-01-01"},
    "amit verma": {"id": "EMP003", "join_date": "2024-01-01"},
    "sneha reddy": {"id": "EMP004", "join_date": "2024-01-01"},
    "vikram joshi": {"id": "EMP005", "join_date": "2024-09-01"},
    "kavita nair": {"id": "EMP006", "join_date": "2024-01-01"},
    "suresh patil": {"id": "EMP007", "join_date": "2024-01-01"},
    "ravi menon": {"id": "EMP008", "join_date": "2024-01-01"},
    "anita desai": {"id": "EMP009", "join_date": "2024-01-01"},
    "deepak shah": {"id": "EMP010", "join_date": "2024-01-01"},
}


@router.post("")
async def submit_claim(
    member_id: Optional[str] = Form(None),
    member_name: Optional[str] = Form(None),
    treatment_date: Optional[str] = Form(None),
    claim_amount: Optional[float] = Form(None),
    hospital: Optional[str] = Form(None),
    cashless_request: bool = Form(False),
    member_join_date: Optional[str] = Form(None),
    documents_json: Optional[str] = Form(None),
    files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    """Submit a new OPD claim for adjudication."""
    claim_id = f"CLM_{uuid.uuid4().hex[:5].upper()}"

    # Save uploaded files
    uploaded_files = []
    upload_dir = os.path.join(settings.upload_dir, claim_id)
    os.makedirs(upload_dir, exist_ok=True)

    for f in files:
        content = await f.read()
        filepath = os.path.join(upload_dir, f.filename)
        with open(filepath, "wb") as out:
            out.write(content)
        uploaded_files.append((content, f.filename))

    # Pre-extract data from uploaded files if form fields are missing
    extracted_data = {}
    if uploaded_files and (not member_name or not treatment_date or claim_amount is None):
        from backend.services.ocr_service import process_multiple_documents
        from backend.services.extraction_service import extract_claim_data

        logger.info(f"[{claim_id}] Pre-extracting data from {len(uploaded_files)} files...")
        ocr_results = process_multiple_documents(uploaded_files)
        if ocr_results:
            combined_text = "\n\n".join(r["text"] for r in ocr_results if r.get("text"))
            if combined_text:
                extracted_data = extract_claim_data(combined_text) or {}

    # Map extracted data to form fields if they are missing
    ext_name = extracted_data.get("patient_name")
    if not member_name and ext_name:
        member_name = ext_name
    
    if not treatment_date and extracted_data.get("treatment_date"):
        treatment_date = extracted_data.get("treatment_date")
        
    if claim_amount is None and extracted_data.get("total_amount") is not None:
        try:
            claim_amount = float(extracted_data.get("total_amount"))
        except (ValueError, TypeError):
            claim_amount = 0.0

    if not hospital and extracted_data.get("clinic_name"):
        hospital = extracted_data.get("clinic_name")

    # Member and join date lookup
    if member_name:
        name_lower = member_name.lower().strip()
        match = MOCK_MEMBERS.get(name_lower)
        if match:
            if not member_id:
                member_id = match["id"]
            if not member_join_date:
                member_join_date = match["join_date"]

    if not member_join_date and member_id:
        member_id_upper = member_id.upper().strip()
        for key, val in MOCK_MEMBERS.items():
            if val["id"] == member_id_upper:
                member_join_date = val["join_date"]
                break

    # Fallback default values if still missing
    if not member_id:
        member_id = "EMP_TEMP"
    if not member_name:
        member_name = "Unknown Patient"
    if not treatment_date:
        from datetime import datetime
        treatment_date = datetime.now().strftime("%Y-%m-%d")
    if claim_amount is None:
        claim_amount = 0.0
    if not member_join_date:
        member_join_date = "2024-01-01"

    # Parse documents JSON if provided
    import json
    documents = {}
    if documents_json:
        try:
            documents = json.loads(documents_json)
        except json.JSONDecodeError:
            pass

    # Create claim record
    claim = Claim(
        claim_id=claim_id,
        member_id=member_id,
        member_name=member_name,
        member_join_date=member_join_date,
        treatment_date=treatment_date,
        claim_amount=claim_amount,
        hospital=hospital or "",
        cashless_request=1 if cashless_request else 0,
        documents=documents,
        status=ClaimStatus.PROCESSING.value,
    )
    db.add(claim)
    db.commit()

    # Run adjudication
    try:
        claim_data = {
            "claim_id": claim_id,
            "member_id": member_id,
            "member_name": member_name,
            "member_join_date": member_join_date,
            "treatment_date": treatment_date,
            "claim_amount": claim_amount,
            "hospital": hospital or "",
            "cashless_request": cashless_request,
            "documents": documents,
            "extracted_data": extracted_data,
        }

        result = adjudicate_claim(claim_data, uploaded_files=uploaded_files or None)

        # Save decision
        decision = Decision(
            claim_id=claim_id,
            decision=result["decision"],
            approved_amount=result.get("approved_amount", 0),
            claimed_amount=claim_amount,
            rejection_reasons=result.get("rejection_reasons", []),
            rejected_items=result.get("rejected_items", []),
            deductions=result.get("deductions", {}),
            flags=result.get("flags", []),
            confidence_score=result.get("confidence_score", 0),
            notes=result.get("notes", ""),
            next_steps=result.get("next_steps", ""),
            eligibility_result=result.get("eligibility_result"),
            coverage_result=result.get("coverage_result"),
            limits_result=result.get("limits_result"),
            medical_necessity_result=result.get("medical_necessity_result"),
            fraud_result=result.get("fraud_result"),
            cashless_approved=1 if result.get("cashless_approved") else 0,
            network_discount=result.get("network_discount", 0),
            processing_time_ms=result.get("processing_time_ms", 0),
        )
        db.add(decision)

        claim.status = ClaimStatus.ADJUDICATED.value
        claim.extracted_data = result.get("extracted_data")
        db.commit()

        return {"claim_id": claim_id, "status": "adjudicated", "decision": decision.to_dict()}

    except Exception as e:
        logger.error(f"Adjudication failed for {claim_id}: {e}")
        claim.status = "ERROR"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Adjudication failed: {str(e)}")


@router.post("/json")
def submit_claim_json(claim_data: dict, db: Session = Depends(get_db)):
    """Submit claim via JSON (for test cases and API integrations)."""
    claim_id = claim_data.get("claim_id", f"CLM_{uuid.uuid4().hex[:5].upper()}")
    claim_data["claim_id"] = claim_id

    claim = Claim(
        claim_id=claim_id,
        member_id=claim_data.get("member_id", ""),
        member_name=claim_data.get("member_name", ""),
        member_join_date=claim_data.get("member_join_date"),
        treatment_date=claim_data.get("treatment_date", ""),
        claim_amount=claim_data.get("claim_amount", 0),
        hospital=claim_data.get("hospital", ""),
        cashless_request=1 if claim_data.get("cashless_request") else 0,
        previous_claims_same_day=claim_data.get("previous_claims_same_day", 0),
        documents=claim_data.get("documents", {}),
        status=ClaimStatus.PROCESSING.value,
    )
    db.add(claim)
    db.commit()

    result = adjudicate_claim(claim_data)

    decision = Decision(
        claim_id=claim_id, decision=result["decision"],
        approved_amount=result.get("approved_amount", 0), claimed_amount=claim_data.get("claim_amount", 0),
        rejection_reasons=result.get("rejection_reasons", []), rejected_items=result.get("rejected_items", []),
        deductions=result.get("deductions", {}), flags=result.get("flags", []),
        confidence_score=result.get("confidence_score", 0), notes=result.get("notes", ""),
        next_steps=result.get("next_steps", ""),
        eligibility_result=result.get("eligibility_result"), coverage_result=result.get("coverage_result"),
        limits_result=result.get("limits_result"), medical_necessity_result=result.get("medical_necessity_result"),
        fraud_result=result.get("fraud_result"),
        cashless_approved=1 if result.get("cashless_approved") else 0,
        network_discount=result.get("network_discount", 0),
        processing_time_ms=result.get("processing_time_ms", 0),
    )
    db.add(decision)
    claim.status = ClaimStatus.ADJUDICATED.value
    claim.extracted_data = result.get("extracted_data")
    db.commit()

    return {"claim_id": claim_id, "status": "adjudicated", "decision": decision.to_dict()}


@router.get("")
def list_claims(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all claims with pagination."""
    claims = db.query(Claim).order_by(Claim.created_at.desc()).offset(skip).limit(limit).all()
    total = db.query(Claim).count()
    return {"claims": [c.to_dict() for c in claims], "total": total}


@router.get("/{claim_id}")
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    """Get claim details by ID."""
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    decision = db.query(Decision).filter(Decision.claim_id == claim_id).first()
    return {
        "claim": claim.to_dict(),
        "decision": decision.to_dict() if decision else None,
    }
