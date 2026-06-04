"""Tests for appeal workflow."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.appeal_service import create_appeal


def test_create_appeal():
    appeal = create_appeal("CLM_TEST1", "The treatment was medically necessary", "Additional doctor note")
    assert appeal["claim_id"] == "CLM_TEST1"
    assert appeal["status"] == "SUBMITTED"
    assert "APL_" in appeal["appeal_id"]
    print(f"✅ Appeal creation test passed: {appeal['appeal_id']}")


if __name__ == "__main__":
    test_create_appeal()
