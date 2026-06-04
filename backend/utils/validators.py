"""Validation utilities."""

import re
from datetime import datetime, date
from typing import Optional
from backend.utils.logger import get_logger

logger = get_logger("validators")


def validate_doctor_registration(reg_number: str) -> bool:
    """
    Validate doctor registration number format.
    Expected format: [StateCode]/[Number]/[Year] e.g., KA/12345/2015
    Also accepts AYUR/ prefix for Ayurvedic practitioners.
    """
    if not reg_number:
        return False

    patterns = [
        r"^[A-Z]{2}/\d{4,6}/\d{4}$",           # Standard: KA/12345/2015
        r"^AYUR/[A-Z]{2}/\d{4,6}/\d{4}$",       # Ayurvedic: AYUR/KL/2345/2019
        r"^[A-Z]{2,4}/\d{4,6}/\d{4}$",          # Flexible state code
    ]

    for pattern in patterns:
        if re.match(pattern, reg_number.strip()):
            return True

    logger.warning(f"Invalid doctor registration format: {reg_number}")
    return False


def validate_treatment_date(
    treatment_date: str,
    policy_start_date: str = "2024-01-01",
    submission_date: Optional[str] = None,
) -> dict:
    """
    Validate treatment date against policy and submission timeline.
    Returns dict with 'valid' boolean and any 'issues' found.
    """
    issues = []

    try:
        treat_dt = _parse_date(treatment_date)
        policy_dt = _parse_date(policy_start_date)

        if treat_dt < policy_dt:
            issues.append("Treatment date is before policy start date")

        if treat_dt > datetime.now().date():
            issues.append("Treatment date is in the future")

        if submission_date:
            sub_dt = _parse_date(submission_date)
            delta = (sub_dt - treat_dt).days
            if delta > 30:
                issues.append(f"Submitted {delta} days after treatment (max 30 days)")

    except (ValueError, TypeError) as e:
        issues.append(f"Invalid date format: {str(e)}")

    return {"valid": len(issues) == 0, "issues": issues}


def validate_claim_amount(amount: float, per_claim_limit: float = 5000) -> dict:
    """Validate claim amount against limits."""
    issues = []

    if amount <= 0:
        issues.append("Claim amount must be positive")
    if amount < 500:
        issues.append("Claim amount below minimum threshold of ₹500")
    if amount > per_claim_limit:
        issues.append(
            f"Claim amount ₹{amount} exceeds per-claim limit of ₹{per_claim_limit}"
        )

    return {"valid": len(issues) == 0, "issues": issues}


def validate_member_id(member_id: str) -> bool:
    """Validate member ID format."""
    if not member_id:
        return False
    return bool(re.match(r"^EMP\d{3,6}$", member_id.strip()))


def validate_documents(documents: dict) -> dict:
    """
    Validate that required documents are present.
    Returns dict with 'valid' boolean and 'missing' documents list.
    """
    required = ["prescription"]
    recommended = ["bill"]
    missing = []
    warnings = []

    for doc in required:
        if doc not in documents or not documents[doc]:
            missing.append(doc)

    for doc in recommended:
        if doc not in documents or not documents[doc]:
            warnings.append(f"Recommended document missing: {doc}")

    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
    }


def _parse_date(date_str: str) -> date:
    """Parse date string in various formats."""
    if isinstance(date_str, date):
        return date_str

    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Cannot parse date: {date_str}")
