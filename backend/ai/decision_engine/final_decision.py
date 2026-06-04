"""Final claim decision generation."""

from backend.utils.constants import DecisionType, CONFIDENCE_THRESHOLD_AUTO, HIGH_VALUE_CLAIM_THRESHOLD
from backend.utils.logger import get_logger

logger = get_logger("final_decision")


def generate_final_decision(
    claim_amount, eligibility_result, coverage_result, limits_result,
    medical_necessity_result, fraud_result, confidence_score,
    cashless_request=False, hospital="",
):
    """Aggregate all check results and produce final decision."""
    all_rejection_codes = []
    all_checks = []
    flags = []
    excluded_items = []
    notes_parts = []

    # Gather from eligibility
    if not eligibility_result.get("passed", True):
        all_rejection_codes.extend(eligibility_result.get("rejection_codes", []))
    all_checks.extend(eligibility_result.get("checks", []))

    # Gather from coverage
    if not coverage_result.get("passed", True):
        all_rejection_codes.extend(coverage_result.get("rejection_codes", []))
    excluded_items = coverage_result.get("excluded_items", [])
    all_checks.extend(coverage_result.get("checks", []))

    # Gather from limits
    if not limits_result.get("passed", True):
        all_rejection_codes.extend(limits_result.get("rejection_codes", []))
    all_checks.extend(limits_result.get("checks", []))

    approved_amount = limits_result.get("approved_amount", claim_amount)
    deductions = limits_result.get("deductions", {})
    network_discount = limits_result.get("network_discount", 0)

    # Gather from medical necessity
    if not medical_necessity_result.get("passed", True):
        all_rejection_codes.extend(medical_necessity_result.get("rejection_codes", []))
    all_checks.extend(medical_necessity_result.get("checks", []))

    # Gather from fraud
    if fraud_result.get("flags"):
        flags = fraud_result["flags"]

    # De-duplicate rejection codes
    all_rejection_codes = list(dict.fromkeys(all_rejection_codes))

    # Determine decision type
    decision, notes = _determine_decision(
        all_rejection_codes, excluded_items, approved_amount, claim_amount,
        confidence_score, flags, cashless_request
    )

    # Cashless handling
    cashless_approved = False
    if cashless_request and decision in [DecisionType.APPROVED, DecisionType.PARTIAL]:
        from backend.utils.parsers import load_json_file
        from backend.config import get_settings
        policy = load_json_file(get_settings().policy_terms_path)
        network_hospitals = policy.get("network_hospitals", [])
        if hospital in network_hospitals:
            cashless_approved = True

    # Build next steps
    next_steps = _generate_next_steps(decision, all_rejection_codes, flags)

    return {
        "decision": decision,
        "approved_amount": round(approved_amount, 2) if decision != DecisionType.REJECTED else 0,
        "claimed_amount": claim_amount,
        "rejection_reasons": all_rejection_codes,
        "rejected_items": excluded_items,
        "deductions": deductions,
        "flags": flags,
        "confidence_score": round(confidence_score, 3),
        "notes": notes,
        "next_steps": next_steps,
        "cashless_approved": cashless_approved,
        "network_discount": network_discount,
        "all_checks": all_checks,
    }


def _determine_decision(rejection_codes, excluded_items, approved_amount, claim_amount, confidence, flags, cashless):
    from backend.config import get_policy_config
    policy = get_policy_config()

    # Priority 1: Fraud → manual review
    if flags and len(flags) >= 2:
        return DecisionType.MANUAL_REVIEW, "Multiple fraud indicators detected, sent for manual review"

    # Priority 2: Low confidence → manual review
    confidence_threshold = policy.get("confidence_threshold_manual", 0.70)
    if confidence < confidence_threshold:
        return DecisionType.MANUAL_REVIEW, f"Confidence score {confidence:.2f} below threshold {confidence_threshold}"

    # Priority 3: High value → manual review
    high_value_limit = policy.get("cashless_claim_limit", 10000)
    if claim_amount > high_value_limit:
        return DecisionType.MANUAL_REVIEW, f"High-value claim (₹{claim_amount}) requires manual review (limit: ₹{high_value_limit})"

    # Priority 4: All rejected
    if rejection_codes and not excluded_items:
        reasons_str = ", ".join(rejection_codes)
        return DecisionType.REJECTED, f"Claim rejected: {reasons_str}"

    # Priority 5: Partial (some items excluded but some covered)
    if excluded_items and approved_amount > 0 and not rejection_codes:
        return DecisionType.PARTIAL, f"Partial approval: excluded items: {', '.join(excluded_items)}"

    # Priority 6: Limits exceeded but partial possible
    if "PER_CLAIM_EXCEEDED" in rejection_codes:
        per_claim_limit = policy.get("per_claim_limit", 5000)
        return DecisionType.REJECTED, f"Claim amount exceeds per-claim limit of ₹{per_claim_limit}"

    # Priority 7: Clean approval
    if not rejection_codes:
        if excluded_items:
            return DecisionType.PARTIAL, f"Approved with exclusions: {', '.join(excluded_items)}"
        return DecisionType.APPROVED, "All checks passed. Claim approved."

    return DecisionType.REJECTED, f"Rejected: {', '.join(rejection_codes)}"


def _generate_next_steps(decision, rejection_codes, flags):
    if decision == DecisionType.APPROVED:
        return "Claim approved. Amount will be processed within 5-7 business days."
    elif decision == DecisionType.PARTIAL:
        return "Partial claim approved. Excluded items are not covered. You may appeal the decision."
    elif decision == DecisionType.MANUAL_REVIEW:
        return "Claim sent for manual review. A reviewer will process within 2-3 business days."
    else:
        steps = ["Claim rejected."]
        if "MISSING_DOCUMENTS" in rejection_codes:
            steps.append("Please resubmit with all required documents.")
        if "WAITING_PERIOD" in rejection_codes:
            steps.append("Please wait until the waiting period is satisfied.")
        if "PER_CLAIM_EXCEEDED" in rejection_codes:
            steps.append("Consider splitting into smaller claims within the per-claim limit.")
        steps.append("You may file an appeal if you disagree with this decision.")
        return " ".join(steps)
