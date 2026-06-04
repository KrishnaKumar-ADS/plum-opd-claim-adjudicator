"""Tests for fraud detection."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.fraud_service import detect_fraud


def test_clean_claim():
    result = detect_fraud("EMP001", 1500, "2024-11-01", previous_claims_same_day=0)
    assert not result["is_suspicious"]
    assert len(result["flags"]) == 0
    print("✅ Clean claim fraud test passed")


def test_suspicious_claim():
    result = detect_fraud("EMP008", 4800, "2024-10-30", previous_claims_same_day=3)
    assert result["is_suspicious"]
    assert len(result["flags"]) >= 2
    print(f"✅ Suspicious claim test passed: {result['flags']}")


if __name__ == "__main__":
    test_clean_claim()
    test_suspicious_claim()
