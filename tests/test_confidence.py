"""Tests for confidence scoring."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.confidence_service import calculate_confidence


def test_high_confidence():
    score = calculate_confidence(
        eligibility_result={"passed": True, "checks": []},
        coverage_result={"passed": True, "checks": [], "excluded_items": [], "covered_items": ["consultation"]},
        limits_result={"passed": True, "checks": []},
        medical_necessity_result={"passed": True, "checks": [{"check": "ai_medical_necessity", "confidence": 0.95}]},
        fraud_result={"risk_score": 0, "flags": []},
        has_documents=True,
    )
    assert score >= 0.8, f"Expected high confidence, got {score}"
    print(f"✅ High confidence test passed: {score}")


def test_low_confidence():
    score = calculate_confidence(
        eligibility_result={"passed": True, "checks": []},
        coverage_result={"passed": True, "checks": [], "excluded_items": ["item1"], "covered_items": ["item2"]},
        limits_result={"passed": True, "checks": []},
        medical_necessity_result={"passed": True, "checks": [{"check": "ai_medical_necessity", "confidence": 0.4}]},
        fraud_result={"risk_score": 0.5, "flags": ["flag1"]},
        has_documents=False,
    )
    assert score < 0.8, f"Expected lower confidence, got {score}"
    print(f"✅ Low confidence test passed: {score}")


if __name__ == "__main__":
    test_high_confidence()
    test_low_confidence()
