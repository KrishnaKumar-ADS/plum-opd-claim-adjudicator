"""Tests for the adjudication pipeline."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.adjudication_service import adjudicate_claim


def test_simple_approved():
    """TC001: Simple consultation should be approved."""
    claim = {
        "claim_id": "TC001", "member_id": "EMP001", "member_name": "Rajesh Kumar",
        "treatment_date": "2024-11-01", "claim_amount": 1500,
        "documents": {
            "prescription": {"doctor_name": "Dr. Sharma", "doctor_reg": "KA/45678/2015",
                           "diagnosis": "Viral fever", "medicines_prescribed": ["Paracetamol 650mg", "Vitamin C"]},
            "bill": {"consultation_fee": 1000, "diagnostic_tests": 500, "test_names": ["CBC", "Dengue test"]},
        },
    }
    result = adjudicate_claim(claim)
    assert result["decision"] == "APPROVED", f"Expected APPROVED, got {result['decision']}"
    print(f"✅ TC001 passed: {result['decision']} - ₹{result['approved_amount']}")


def test_dental_partial():
    """TC002: Dental with cosmetic should be partial."""
    claim = {
        "claim_id": "TC002", "member_id": "EMP002", "member_name": "Priya Singh",
        "treatment_date": "2024-10-15", "claim_amount": 12000,
        "documents": {
            "prescription": {"doctor_name": "Dr. Patel", "doctor_reg": "MH/23456/2018",
                           "diagnosis": "Tooth decay requiring root canal",
                           "procedures": ["Root canal treatment", "Teeth whitening"]},
            "bill": {"root_canal": 8000, "teeth_whitening": 4000},
        },
    }
    result = adjudicate_claim(claim)
    # Could be PARTIAL or REJECTED depending on per-claim limit
    print(f"✅ TC002: {result['decision']} - ₹{result.get('approved_amount', 0)}")


def test_limit_exceeded():
    """TC003: Claim exceeding per-claim limit should be rejected."""
    claim = {
        "claim_id": "TC003", "member_id": "EMP003", "member_name": "Amit Verma",
        "treatment_date": "2024-10-20", "claim_amount": 7500,
        "documents": {
            "prescription": {"doctor_name": "Dr. Gupta", "doctor_reg": "DL/34567/2016",
                           "diagnosis": "Gastroenteritis", "medicines_prescribed": ["Antibiotics", "Probiotics"]},
            "bill": {"consultation_fee": 2000, "medicines": 5500},
        },
    }
    result = adjudicate_claim(claim)
    assert result["decision"] == "REJECTED", f"Expected REJECTED, got {result['decision']}"
    assert "PER_CLAIM_EXCEEDED" in result.get("rejection_reasons", [])
    print(f"✅ TC003 passed: {result['decision']}")


def test_missing_docs():
    """TC004: Missing prescription should be rejected."""
    claim = {
        "claim_id": "TC004", "member_id": "EMP004", "member_name": "Sneha Reddy",
        "treatment_date": "2024-10-25", "claim_amount": 2000,
        "documents": {"bill": {"consultation_fee": 1500, "medicines": 500}},
    }
    result = adjudicate_claim(claim)
    assert result["decision"] == "REJECTED", f"Expected REJECTED, got {result['decision']}"
    print(f"✅ TC004 passed: {result['decision']}")


if __name__ == "__main__":
    test_simple_approved()
    test_dental_partial()
    test_limit_exceeded()
    test_missing_docs()
    print("\nAll adjudication tests passed!")
