"""Fraud detection indicators."""

from backend.utils.constants import FraudFlag
from backend.utils.logger import get_logger

logger = get_logger("fraud_service")


def detect_fraud(
    member_id: str, claim_amount: float, treatment_date: str,
    previous_claims_same_day: int = 0, diagnosis: str = "",
    doctor_reg: str = "", hospital: str = "", extracted_data: dict = None,
) -> dict:
    """Detect fraud indicators in a claim."""
    flags = []
    risk_score = 0.0

    # 1. Multiple claims same day
    if previous_claims_same_day >= 3:
        flags.append(FraudFlag.MULTIPLE_CLAIMS_SAME_DAY.value)
        risk_score += 0.3

    # 2. High frequency (simplified — in production, check DB)
    if previous_claims_same_day >= 2:
        flags.append(FraudFlag.UNUSUAL_PATTERN.value)
        risk_score += 0.2

    # 3. Blacklisted provider check (simplified)
    blacklisted = ["FAKE/00000/0000", "XX/99999/9999"]
    if doctor_reg in blacklisted:
        flags.append(FraudFlag.BLACKLISTED_PROVIDER.value)
        risk_score += 0.5

    # 4. Document quality concerns
    if extracted_data:
        quality = extracted_data.get("document_quality", "good")
        if quality == "poor":
            flags.append(FraudFlag.SUSPICIOUS_ALTERATIONS.value)
            risk_score += 0.2

    # 5. Amount anomaly (very high for OPD)
    if claim_amount > 20000:
        risk_score += 0.1

    # 6. Diagnosis not matching age/gender (Diagnosis Mismatch)
    if extracted_data and diagnosis:
        gender = str(extracted_data.get("patient_gender", "") or "").lower()
        diag_lower = diagnosis.lower()
        
        # Gender mismatch rules
        if "male" in gender and not "female" in gender: # Exact male
            if any(kw in diag_lower for kw in ["pregnancy", "maternity", "obstetric", "ovarian", "uterine", "cervix"]):
                flags.append(FraudFlag.DIAGNOSIS_MISMATCH.value)
                risk_score += 0.4
        elif "female" in gender:
            if any(kw in diag_lower for kw in ["prostate", "testicular", "seminal"]):
                flags.append(FraudFlag.DIAGNOSIS_MISMATCH.value)
                risk_score += 0.4

    # 7. Duplicate bills across different dates
    try:
        from backend.database import SessionLocal
        from backend.models.claim import Claim
        db = SessionLocal()
        # Find other claims for the same member with the same claim amount on different dates
        dup_claims = db.query(Claim).filter(
            Claim.member_id == member_id,
            Claim.claim_amount == claim_amount,
            Claim.treatment_date != treatment_date
        ).all()
        if dup_claims:
            flags.append(FraudFlag.DUPLICATE_BILLS.value)
            risk_score += 0.4
        db.close()
    except Exception as e:
        logger.warning(f"Error checking duplicate claims: {e}")

    risk_score = min(risk_score, 1.0)

    from backend.config import get_policy_config
    policy = get_policy_config()
    fraud_risk_threshold = policy.get("fraud_risk_threshold", 0.6)

    return {
        "flags": flags,
        "risk_score": round(risk_score, 2),
        "is_suspicious": len(flags) >= 2 or risk_score > fraud_risk_threshold,
        "recommend_manual_review": len(flags) >= 2,
        "step": "fraud_detection",
    }
