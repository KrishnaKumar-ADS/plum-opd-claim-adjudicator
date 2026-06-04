"""Coverage validation."""

import json
from pathlib import Path
from typing import Optional
from backend.config import get_settings
from backend.utils.parsers import load_json_file
from backend.utils.logger import get_logger

logger = get_logger("coverage")
settings = get_settings()

# Load policy terms at module level
_policy_terms: Optional[dict] = None


def _get_policy_terms() -> dict:
    """Lazy-load policy terms."""
    global _policy_terms
    if _policy_terms is None:
        _policy_terms = load_json_file(settings.policy_terms_path)
        if not _policy_terms:
            logger.warning("Policy terms not loaded, using defaults")
            _policy_terms = {}
    return _policy_terms


# Exclusions list from policy
EXCLUSIONS = [
    "cosmetic procedures", "weight loss treatments", "infertility treatments",
    "experimental treatments", "self-inflicted injuries", "adventure sports injuries",
    "war and nuclear risks", "hiv/aids treatment", "alcoholism/drug abuse treatment",
    "non-allopathic treatments (except listed)",
    "vitamins and supplements (unless prescribed for deficiency)",
]

# Covered service categories
COVERED_SERVICES = [
    "consultation", "diagnostic tests", "pharmacy", "medicines",
    "dental", "vision", "alternative medicine", "ayurveda",
    "homeopathy", "unani", "blood tests", "urine tests",
    "x-rays", "ecg", "ultrasound", "filling", "extraction",
    "root canal", "cleaning", "eye test", "glasses", "contact lenses",
]

# Services requiring pre-authorization
PRE_AUTH_REQUIRED = ["mri", "ct scan", "mri lumbar spine", "ct scan brain"]


def check_coverage(
    diagnosis: str,
    treatments: list[str],
    procedures: list[str] = None,
    medicines: list[str] = None,
    claim_amount: float = 0,
) -> dict:
    """
    Verify if the treatment/services are covered under the policy.

    Returns dict with:
        - passed: bool
        - covered_items: list of covered treatments
        - excluded_items: list of excluded treatments
        - rejection_codes: list of codes
        - pre_auth_needed: list of items requiring pre-authorization
    """
    checks = []
    rejection_codes = []
    covered_items = []
    excluded_items = []
    pre_auth_needed = []

    all_items = list(treatments or [])
    if procedures:
        all_items.extend(procedures)

    # 1. Check each treatment/procedure against exclusions
    for item in all_items:
        item_lower = item.lower().strip()

        # Check exclusions
        is_excluded = False
        for exclusion in EXCLUSIONS:
            if _is_match(item_lower, exclusion):
                excluded_items.append(f"{item} - {exclusion}")
                is_excluded = True
                break

        if not is_excluded:
            # Check if it's a covered service
            covered_items.append(item)

        # Check pre-authorization
        for pre_auth_item in PRE_AUTH_REQUIRED:
            if pre_auth_item in item_lower:
                pre_auth_needed.append(item)

    # 2. Check diagnosis against exclusions
    diagnosis_excluded = _check_diagnosis_exclusion(diagnosis)
    if diagnosis_excluded:
        checks.append({
            "check": "diagnosis_exclusion",
            "passed": False,
            "detail": f"Diagnosis '{diagnosis}' matches exclusion: {diagnosis_excluded}",
        })
        rejection_codes.append("EXCLUDED_CONDITION")

    # 3. Determine overall result
    if excluded_items and not covered_items:
        rejection_codes.append("SERVICE_NOT_COVERED")
        checks.append({
            "check": "service_coverage",
            "passed": False,
            "detail": f"All items excluded: {excluded_items}",
        })
    elif excluded_items and covered_items:
        checks.append({
            "check": "service_coverage",
            "passed": True,
            "detail": f"Partial coverage: covered={covered_items}, excluded={excluded_items}",
        })
    else:
        checks.append({
            "check": "service_coverage",
            "passed": True,
            "detail": f"All items covered: {covered_items}",
        })

    # 4. Pre-authorization check
    if pre_auth_needed and claim_amount > 10000:
        rejection_codes.append("PRE_AUTH_MISSING")
        checks.append({
            "check": "pre_authorization",
            "passed": False,
            "detail": f"Pre-authorization required for: {pre_auth_needed} (claim > ₹10,000)",
        })
    elif pre_auth_needed:
        checks.append({
            "check": "pre_authorization",
            "passed": True,
            "detail": f"Pre-auth items found but claim ≤ ₹10,000: {pre_auth_needed}",
        })

    overall_passed = len(rejection_codes) == 0

    return {
        "passed": overall_passed,
        "checks": checks,
        "rejection_codes": rejection_codes,
        "covered_items": covered_items,
        "excluded_items": excluded_items,
        "pre_auth_needed": pre_auth_needed,
        "step": "coverage",
    }


def _check_diagnosis_exclusion(diagnosis: str) -> Optional[str]:
    """Check if the diagnosis itself maps to an excluded condition."""
    diagnosis_lower = diagnosis.lower().strip()

    exclusion_mappings = {
        "obesity": "Weight loss treatments",
        "weight loss": "Weight loss treatments",
        "bariatric": "Weight loss treatments",
        "cosmetic": "Cosmetic procedures",
        "aesthetic": "Cosmetic procedures",
        "teeth whitening": "Cosmetic procedures",
        "infertility": "Infertility treatments",
        "ivf": "Infertility treatments",
        "experimental": "Experimental treatments",
        "lasik": "Not covered under vision plan",
    }

    for keyword, exclusion in exclusion_mappings.items():
        if keyword in diagnosis_lower:
            return exclusion

    return None


def _is_match(item: str, exclusion: str) -> bool:
    """Fuzzy match an item against an exclusion rule."""
    item_words = set(item.lower().split())
    exclusion_words = set(exclusion.lower().split())

    # Check for key word overlap
    overlap = item_words & exclusion_words
    if len(overlap) >= 2:
        return True

    # Direct substring check
    if exclusion in item.lower() or item.lower() in exclusion:
        return True

    # Specific cosmetic checks
    cosmetic_terms = ["whitening", "bleaching", "cosmetic", "aesthetic", "botox", "filler"]
    if any(term in item.lower() for term in cosmetic_terms):
        return exclusion == "cosmetic procedures"

    return False
