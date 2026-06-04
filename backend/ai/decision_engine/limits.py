"""Policy limits validation."""

from typing import Optional
from backend.config import get_settings
from backend.utils.parsers import load_json_file
from backend.utils.logger import get_logger

logger = get_logger("limits")
settings = get_settings()

# Default limits from policy_terms.json
DEFAULT_LIMITS = {
    "annual_limit": 50000,
    "per_claim_limit": 5000,
    "family_floater_limit": 150000,
    "sub_limits": {
        "consultation_fees": {"limit": 2000, "copay_pct": 10},
        "diagnostic_tests": {"limit": 10000, "copay_pct": 0},
        "pharmacy": {"limit": 15000, "copay_pct": 0, "branded_copay_pct": 30},
        "dental": {"limit": 10000, "copay_pct": 0, "routine_checkup_limit": 2000},
        "vision": {"limit": 5000, "copay_pct": 0},
        "alternative_medicine": {"limit": 8000, "copay_pct": 0},
    },
}

# Category mapping for bill breakdown items
CATEGORY_MAPPING = {
    "consultation_fee": "consultation_fees",
    "consultation": "consultation_fees",
    "diagnostic_tests": "diagnostic_tests",
    "diagnostic": "diagnostic_tests",
    "blood_test": "diagnostic_tests",
    "x_ray": "diagnostic_tests",
    "mri_scan": "diagnostic_tests",
    "medicines": "pharmacy",
    "pharmacy": "pharmacy",
    "root_canal": "dental",
    "dental": "dental",
    "teeth_whitening": "dental",
    "filling": "dental",
    "eye_test": "vision",
    "glasses": "vision",
    "therapy_charges": "alternative_medicine",
}


def check_limits(
    claim_amount: float,
    bill_breakdown: dict = None,
    ytd_claims: float = 0,
    category: str = "general",
    hospital: str = "",
    is_network: bool = False,
    excluded_items: list = None,
) -> dict:
    """
    Validate claim amount against all applicable limits.

    Args:
        claim_amount: Total claim amount
        bill_breakdown: Dict of bill categories and amounts
        ytd_claims: Year-to-date claims total for this member
        category: Service category (consultation, pharmacy, dental, etc.)
        hospital: Hospital name
        is_network: Whether it's a network hospital
        excluded_items: List of coverage exclusions to deduct

    Returns dict with:
        - passed: bool
        - approved_amount: adjusted amount after limits/copay
        - deductions: breakdown of deductions
        - rejection_codes: list of codes
    """
    checks = []
    rejection_codes = []
    deductions = {}
    approved_amount = claim_amount

    # 0. Deduct excluded items from starting approved amount and filter them out
    active_bill_breakdown = {}
    if bill_breakdown:
        for item_name, amount in bill_breakdown.items():
            is_item_excluded = False
            if excluded_items:
                for excl in excluded_items:
                    excl_lower = excl.lower()
                    name_lower = item_name.lower().replace("_", " ")
                    if name_lower in excl_lower or excl_lower in name_lower:
                        is_item_excluded = True
                        break
            
            if is_item_excluded:
                approved_amount -= amount
                deductions[f"{item_name}_exclusion"] = amount
                checks.append({
                    "check": f"exclusion_{item_name}",
                    "passed": True,
                    "detail": f"{item_name}: ₹{amount} deducted due to coverage exclusion",
                })
            else:
                active_bill_breakdown[item_name] = amount
    else:
        active_bill_breakdown = None

    # Check if this is a specialty claim (dental, vision, alternative medicine, diagnostic tests)
    is_specialty = False
    if active_bill_breakdown:
        specialty_categories = {"dental", "vision", "alternative_medicine", "diagnostic_tests"}
        for item_name in active_bill_breakdown.keys():
            mapped_cat = CATEGORY_MAPPING.get(item_name.lower())
            if mapped_cat in specialty_categories:
                is_specialty = True
                break

    if category in ["dental", "vision", "alternative_medicine", "diagnostic_tests"]:
        is_specialty = True

    # 1. Per-claim limit check
    from backend.config import get_policy_config
    policy = get_policy_config()
    per_claim_limit = policy.get("per_claim_limit", 5000)
    if claim_amount > per_claim_limit and not is_specialty:
        rejection_codes.append("PER_CLAIM_EXCEEDED")
        checks.append({
            "check": "per_claim_limit",
            "passed": False,
            "detail": f"Claim ₹{claim_amount} exceeds per-claim limit of ₹{per_claim_limit}",
        })
    else:
        checks.append({
            "check": "per_claim_limit",
            "passed": True,
            "detail": f"Claim ₹{claim_amount} within limit or specialty bypass active",
        })

    # 2. Annual limit check
    annual_limit = policy.get("annual_limit", 50000)
    total_with_current = ytd_claims + claim_amount
    if total_with_current > annual_limit:
        remaining = max(0, annual_limit - ytd_claims)
        if remaining <= 0:
            rejection_codes.append("ANNUAL_LIMIT_EXCEEDED")
            checks.append({
                "check": "annual_limit",
                "passed": False,
                "detail": f"Annual limit exhausted. YTD: ₹{ytd_claims}, Limit: ₹{annual_limit}",
            })
        else:
            approved_amount = min(approved_amount, remaining)
            checks.append({
                "check": "annual_limit",
                "passed": True,
                "detail": f"Partial: only ₹{remaining} remaining of ₹{annual_limit} annual limit",
            })
    else:
        checks.append({
            "check": "annual_limit",
            "passed": True,
            "detail": f"YTD ₹{ytd_claims} + current ₹{claim_amount} = ₹{total_with_current} within ₹{annual_limit}",
        })

    # 3. Sub-limit checks (if active bill breakdown provided)
    if active_bill_breakdown:
        sub_limit_result = _check_sub_limits(active_bill_breakdown)
        checks.extend(sub_limit_result["checks"])
        deductions.update(sub_limit_result.get("deductions", {}))
        if sub_limit_result.get("rejection_codes"):
            rejection_codes.extend(sub_limit_result["rejection_codes"])
        if sub_limit_result.get("adjusted_total"):
            approved_amount = min(approved_amount, sub_limit_result["adjusted_total"])

    # 4. Co-payment calculation
    copay_result = _calculate_copay(claim_amount, category, active_bill_breakdown, is_network)
    if copay_result["copay_amount"] > 0:
        deductions["copay"] = copay_result["copay_amount"]
        approved_amount -= copay_result["copay_amount"]
        checks.append({
            "check": "copay",
            "passed": True,
            "detail": f"Co-pay of ₹{copay_result['copay_amount']} applied ({copay_result['copay_pct']}%)",
        })

    # 5. Network discount
    network_discount = 0
    if is_network and hospital:
        from backend.utils.parsers import load_json_file
        policy_terms = load_json_file(settings.policy_terms_path)
        network_hospitals = policy_terms.get("network_hospitals", [])
        if hospital in network_hospitals:
            from backend.config import get_policy_config
            dynamic_policy = get_policy_config()
            discount_pct = dynamic_policy.get("network_discount_percentage", 10)
            network_discount = round(claim_amount * discount_pct / 100, 2)
            approved_amount -= network_discount
            deductions["network_discount"] = network_discount
            checks.append({
                "check": "network_discount",
                "passed": True,
                "detail": f"Network discount of {discount_pct}% = ₹{network_discount}",
            })

    # Ensure approved amount is non-negative
    approved_amount = max(0, round(approved_amount, 2))

    overall_passed = len(rejection_codes) == 0

    return {
        "passed": overall_passed,
        "checks": checks,
        "rejection_codes": rejection_codes,
        "approved_amount": approved_amount,
        "claimed_amount": claim_amount,
        "deductions": deductions,
        "network_discount": network_discount,
        "step": "limits",
    }


def _check_sub_limits(bill_breakdown: dict) -> dict:
    """Check individual category sub-limits."""
    checks = []
    rejection_codes = []
    deductions = {}
    adjusted_total = 0

    from backend.config import get_policy_config
    policy = get_policy_config()
    
    import copy
    sub_limits = copy.deepcopy(DEFAULT_LIMITS["sub_limits"])
    if "consultation_fee_limit" in policy:
        sub_limits["consultation_fees"]["limit"] = policy["consultation_fee_limit"]
    if "diagnostic_tests_limit" in policy:
        sub_limits["diagnostic_tests"]["limit"] = policy["diagnostic_tests_limit"]

    for item_name, amount in bill_breakdown.items():
        if not isinstance(amount, (int, float)):
            continue

        # Map to category
        category = CATEGORY_MAPPING.get(item_name.lower(), None)
        if category and category in sub_limits:
            limit_info = sub_limits[category]
            limit = limit_info["limit"]

            if amount > limit:
                capped = limit
                deductions[f"{item_name}_sub_limit_cap"] = amount - limit
                checks.append({
                    "check": f"sub_limit_{category}",
                    "passed": True,
                    "detail": f"{item_name}: ₹{amount} capped to sub-limit ₹{limit}",
                })
                adjusted_total += capped
            else:
                adjusted_total += amount
                checks.append({
                    "check": f"sub_limit_{category}",
                    "passed": True,
                    "detail": f"{item_name}: ₹{amount} within sub-limit ₹{limit}",
                })
        else:
            adjusted_total += amount

    return {
        "checks": checks,
        "rejection_codes": rejection_codes,
        "deductions": deductions,
        "adjusted_total": adjusted_total,
    }


def _calculate_copay(
    claim_amount: float,
    category: str = "general",
    bill_breakdown: dict = None,
    is_network: bool = False,
) -> dict:
    """Calculate co-payment amount."""
    if is_network:
        return {
            "copay_pct": 0,
            "copay_amount": 0,
        }

    from backend.config import get_policy_config
    policy = get_policy_config()
    copay_pct = policy.get("copay_percentage", 20)
    sub_limits = DEFAULT_LIMITS["sub_limits"]

    if bill_breakdown:
        # Check if this is a specialty claim (dental, vision, alternative medicine) for copay purposes
        is_specialty = False
        specialty_categories = {"dental", "vision", "alternative_medicine"}
        for item_name in bill_breakdown.keys():
            mapped_cat = CATEGORY_MAPPING.get(item_name.lower())
            if mapped_cat in specialty_categories:
                is_specialty = True
                break

        if not is_specialty:
            # If there's a consultation fee, apply consultation copay
            if "consultation_fee" in bill_breakdown or "consultation" in bill_breakdown:
                consultation_info = sub_limits.get("consultation_fees", {})
                copay_pct = consultation_info.get("copay_pct", 10)
    else:
        if category == "consultation":
            copay_pct = 10

    copay_amount = round(claim_amount * copay_pct / 100, 2)

    return {
        "copay_pct": copay_pct,
        "copay_amount": copay_amount,
    }
