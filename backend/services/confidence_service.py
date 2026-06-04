"""Confidence score generation."""

from backend.utils.constants import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW
from backend.utils.logger import get_logger

logger = get_logger("confidence_service")


def calculate_confidence(
    eligibility_result: dict, coverage_result: dict, limits_result: dict,
    medical_necessity_result: dict, fraud_result: dict, extracted_data: dict = None,
    has_documents: bool = True,
) -> float:
    """Calculate overall confidence score for the adjudication decision."""
    scores = []
    weights = []

    # 1. Document quality (weight: 0.15)
    doc_score = 1.0 if has_documents else 0.3
    if extracted_data:
        quality = extracted_data.get("document_quality", "good")
        doc_score = {"good": 1.0, "fair": 0.7, "poor": 0.4}.get(quality, 0.7)
    scores.append(doc_score)
    weights.append(0.15)

    # 2. Eligibility clarity (weight: 0.20)
    elig_checks = eligibility_result.get("checks", [])
    elig_score = 1.0 if eligibility_result.get("passed") else 0.95  # Rejections are clear
    scores.append(elig_score)
    weights.append(0.20)

    # 3. Coverage clarity (weight: 0.20)
    coverage_score = 0.9
    if coverage_result.get("excluded_items") and coverage_result.get("covered_items"):
        coverage_score = 0.85  # Partial is less certain
    elif coverage_result.get("passed"):
        coverage_score = 0.95
    scores.append(coverage_score)
    weights.append(0.20)

    # 4. Limits clarity (weight: 0.15)
    limits_score = 0.98 if limits_result.get("passed") is not None else 0.7
    scores.append(limits_score)
    weights.append(0.15)

    # 5. Medical necessity AI confidence (weight: 0.20)
    med_score = 0.8
    for check in medical_necessity_result.get("checks", []):
        if check.get("check") == "ai_medical_necessity":
            med_score = check.get("confidence", 0.8)
            break
    scores.append(med_score)
    weights.append(0.20)

    # 6. Fraud risk inverse (weight: 0.10)
    fraud_risk = fraud_result.get("risk_score", 0)
    fraud_score = max(0, 1.0 - fraud_risk)
    scores.append(fraud_score)
    weights.append(0.10)

    # Weighted average
    total = sum(s * w for s, w in zip(scores, weights))
    total_weight = sum(weights)
    confidence = total / total_weight if total_weight > 0 else 0.5

    confidence = max(0.0, min(1.0, round(confidence, 3)))
    logger.info(f"Confidence score: {confidence} (components: {list(zip(['doc','elig','cov','lim','med','fraud'], scores))})")

    return confidence
