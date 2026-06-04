"""Policy eligibility checks."""

from datetime import datetime, timedelta
from typing import Optional
from backend.utils.logger import get_logger
from backend.utils.validators import _parse_date

logger = get_logger("eligibility")

# Pre-existing disease to waiting period mapping (from policy_terms)
SPECIFIC_WAITING_PERIODS = {
    "diabetes": 90,
    "type 2 diabetes": 90,
    "type 1 diabetes": 90,
    "hypertension": 90,
    "high blood pressure": 90,
    "joint replacement": 730,
    "maternity": 270,
}

INITIAL_WAITING_PERIOD_DAYS = 30
PRE_EXISTING_WAITING_DAYS = 365


def check_eligibility(
    treatment_date: str,
    member_join_date: Optional[str] = None,
    diagnosis: str = "",
    policy_start_date: str = "2024-01-01",
    member_id: str = "",
) -> dict:
    """
    Perform comprehensive eligibility check.

    Returns dict with:
        - passed: bool
        - checks: list of individual check results
        - rejection_codes: list of rejection codes if failed
    """
    checks = []
    rejection_codes = []

    # 1. Policy active check
    policy_check = _check_policy_active(treatment_date, policy_start_date)
    checks.append(policy_check)
    if not policy_check["passed"]:
        rejection_codes.append("POLICY_INACTIVE")

    # 2. Member verification
    member_check = _check_member(member_id)
    checks.append(member_check)
    if not member_check["passed"]:
        rejection_codes.append("MEMBER_NOT_COVERED")

    # 3. Initial waiting period
    if member_join_date:
        waiting_check = _check_initial_waiting_period(treatment_date, member_join_date)
        checks.append(waiting_check)
        if not waiting_check["passed"]:
            rejection_codes.append("WAITING_PERIOD")

    # 4. Condition-specific waiting period
    if diagnosis and member_join_date:
        condition_check = _check_condition_waiting_period(
            treatment_date, member_join_date, diagnosis
        )
        checks.append(condition_check)
        if not condition_check["passed"]:
            if "WAITING_PERIOD" not in rejection_codes:
                rejection_codes.append("WAITING_PERIOD")

    overall_passed = len(rejection_codes) == 0

    return {
        "passed": overall_passed,
        "checks": checks,
        "rejection_codes": rejection_codes,
        "step": "eligibility",
    }


def _check_policy_active(treatment_date: str, policy_start_date: str) -> dict:
    """Check if the policy was active on the treatment date."""
    try:
        treat_dt = _parse_date(treatment_date)
        policy_dt = _parse_date(policy_start_date)

        is_active = treat_dt >= policy_dt and treat_dt <= datetime.now().date()

        return {
            "check": "policy_active",
            "passed": is_active,
            "detail": f"Policy start: {policy_start_date}, Treatment: {treatment_date}",
        }
    except Exception as e:
        return {
            "check": "policy_active",
            "passed": False,
            "detail": f"Date validation error: {e}",
        }


def _check_member(member_id: str) -> dict:
    """Check if the member is covered under the policy."""
    # In a real system, this would check against a member database
    # For MVP, we accept any valid member ID format
    if not member_id:
        return {"check": "member_verification", "passed": True, "detail": "No member ID provided, skipping"}

    is_valid = member_id.startswith("EMP") and len(member_id) >= 4
    return {
        "check": "member_verification",
        "passed": is_valid,
        "detail": f"Member ID: {member_id} - {'valid' if is_valid else 'invalid format'}",
    }


def _check_initial_waiting_period(treatment_date: str, join_date: str) -> dict:
    """Check if the initial waiting period has been satisfied."""
    try:
        from backend.config import get_policy_config
        policy = get_policy_config()
        required_days = policy.get("waiting_period_days", 30)

        treat_dt = _parse_date(treatment_date)
        join_dt = _parse_date(join_date)

        days_since_join = (treat_dt - join_dt).days
        passed = days_since_join >= required_days

        return {
            "check": "initial_waiting_period",
            "passed": passed,
            "detail": (
                f"Joined: {join_date}, Treatment: {treatment_date}, "
                f"Days since join: {days_since_join}, Required: {required_days}"
            ),
        }
    except Exception as e:
        return {"check": "initial_waiting_period", "passed": True, "detail": f"Error: {e}"}


def _check_condition_waiting_period(
    treatment_date: str, join_date: str, diagnosis: str
) -> dict:
    """Check condition-specific waiting periods (e.g., 90 days for diabetes)."""
    try:
        treat_dt = _parse_date(treatment_date)
        join_dt = _parse_date(join_date)

        diagnosis_lower = diagnosis.lower().strip()
        days_since_join = (treat_dt - join_dt).days

        # Check if the diagnosis has a specific waiting period
        for condition, wait_days in SPECIFIC_WAITING_PERIODS.items():
            if condition in diagnosis_lower:
                passed = days_since_join >= wait_days
                eligible_date = join_dt + timedelta(days=wait_days)
                return {
                    "check": "condition_waiting_period",
                    "passed": passed,
                    "detail": (
                        f"Condition: {diagnosis} requires {wait_days}-day waiting period. "
                        f"Days since join: {days_since_join}. "
                        f"Eligible from: {eligible_date.strftime('%Y-%m-%d')}"
                    ),
                }

        return {
            "check": "condition_waiting_period",
            "passed": True,
            "detail": f"No specific waiting period for: {diagnosis}",
        }
    except Exception as e:
        return {"check": "condition_waiting_period", "passed": True, "detail": f"Error: {e}"}
