"""Application constants."""

from enum import Enum


class ClaimStatus(str, Enum):
    """Claim processing status."""
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    ADJUDICATED = "ADJUDICATED"
    APPEALED = "APPEALED"
    CLOSED = "CLOSED"


class DecisionType(str, Enum):
    """Adjudication decision types."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PARTIAL = "PARTIAL"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class AppealStatus(str, Enum):
    """Appeal workflow status."""
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RejectionCode(str, Enum):
    """All possible rejection reason codes."""
    # Eligibility
    POLICY_INACTIVE = "POLICY_INACTIVE"
    WAITING_PERIOD = "WAITING_PERIOD"
    MEMBER_NOT_COVERED = "MEMBER_NOT_COVERED"

    # Documentation
    MISSING_DOCUMENTS = "MISSING_DOCUMENTS"
    ILLEGIBLE_DOCUMENTS = "ILLEGIBLE_DOCUMENTS"
    INVALID_PRESCRIPTION = "INVALID_PRESCRIPTION"
    DOCTOR_REG_INVALID = "DOCTOR_REG_INVALID"
    DATE_MISMATCH = "DATE_MISMATCH"
    PATIENT_MISMATCH = "PATIENT_MISMATCH"

    # Coverage
    SERVICE_NOT_COVERED = "SERVICE_NOT_COVERED"
    EXCLUDED_CONDITION = "EXCLUDED_CONDITION"
    PRE_AUTH_MISSING = "PRE_AUTH_MISSING"

    # Limits
    ANNUAL_LIMIT_EXCEEDED = "ANNUAL_LIMIT_EXCEEDED"
    SUB_LIMIT_EXCEEDED = "SUB_LIMIT_EXCEEDED"
    PER_CLAIM_EXCEEDED = "PER_CLAIM_EXCEEDED"

    # Medical
    NOT_MEDICALLY_NECESSARY = "NOT_MEDICALLY_NECESSARY"
    EXPERIMENTAL_TREATMENT = "EXPERIMENTAL_TREATMENT"
    COSMETIC_PROCEDURE = "COSMETIC_PROCEDURE"

    # Process
    LATE_SUBMISSION = "LATE_SUBMISSION"
    DUPLICATE_CLAIM = "DUPLICATE_CLAIM"
    BELOW_MIN_AMOUNT = "BELOW_MIN_AMOUNT"


class DocumentType(str, Enum):
    """Types of medical documents."""
    PRESCRIPTION = "prescription"
    BILL = "bill"
    DIAGNOSTIC_REPORT = "diagnostic_report"
    PHARMACY_BILL = "pharmacy_bill"
    OTHER = "other"


class FraudFlag(str, Enum):
    """Fraud detection flag types."""
    MULTIPLE_CLAIMS_SAME_DAY = "Multiple claims same day"
    HIGH_FREQUENCY = "Unusually high claim frequency"
    SUSPICIOUS_ALTERATIONS = "Bills with suspicious alterations"
    DIAGNOSIS_MISMATCH = "Diagnosis not matching age/gender"
    DUPLICATE_BILLS = "Duplicate bills across different dates"
    BLACKLISTED_PROVIDER = "Provider not registered/blacklisted"
    UNUSUAL_PATTERN = "Unusual pattern detected"


# Service categories for sub-limit checking
SERVICE_CATEGORIES = {
    "consultation": "consultation_fees",
    "diagnostic": "diagnostic_tests",
    "pharmacy": "pharmacy",
    "dental": "dental",
    "vision": "vision",
    "alternative_medicine": "alternative_medicine",
}

# Confidence thresholds
CONFIDENCE_THRESHOLD_AUTO = 0.70  # Below this → manual review
CONFIDENCE_HIGH = 0.90
CONFIDENCE_MEDIUM = 0.70
CONFIDENCE_LOW = 0.50

# Claim amount thresholds
HIGH_VALUE_CLAIM_THRESHOLD = 25000
MINIMUM_CLAIM_AMOUNT = 500
PER_CLAIM_LIMIT = 5000
ANNUAL_LIMIT = 50000

# Submission deadline (days)
SUBMISSION_DEADLINE_DAYS = 30
