"""Evaluation pipeline."""

from backend.services.adjudication_service import adjudicate_claim
from backend.utils.parsers import load_json_file
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("evaluation_service")

_last_evaluation_results: dict | None = None


def get_last_evaluation_results() -> dict | None:
    """Return the most recent evaluation run results, if any."""
    return _last_evaluation_results


def run_evaluation() -> dict:
    """Run all test cases and compare against expected outputs."""
    global _last_evaluation_results
    settings = get_settings()
    test_data = load_json_file(settings.test_cases_path)
    test_cases = test_data.get("test_cases", [])

    if not test_cases:
        return {"error": "No test cases found", "results": []}

    results = []
    correct = 0
    total = len(test_cases)

    for tc in test_cases:
        case_id = tc.get("case_id", "unknown")
        logger.info(f"Running test case: {case_id} - {tc.get('case_name', '')}")

        try:
            input_data = tc.get("input_data", {})
            expected = tc.get("expected_output", {})

            # Build claim data from test case
            claim_data = {
                "claim_id": case_id,
                "member_id": input_data.get("member_id", ""),
                "member_name": input_data.get("member_name", ""),
                "member_join_date": input_data.get("member_join_date"),
                "treatment_date": input_data.get("treatment_date", ""),
                "claim_amount": input_data.get("claim_amount", 0),
                "hospital": input_data.get("hospital", ""),
                "cashless_request": input_data.get("cashless_request", False),
                "previous_claims_same_day": input_data.get("previous_claims_same_day", 0),
                "documents": input_data.get("documents", {}),
            }

            actual = adjudicate_claim(claim_data)
            is_correct = actual.get("decision") == expected.get("decision")
            if is_correct:
                correct += 1

            results.append({
                "case_id": case_id,
                "case_name": tc.get("case_name", ""),
                "expected_decision": expected.get("decision"),
                "actual_decision": actual.get("decision"),
                "correct": is_correct,
                "expected_amount": expected.get("approved_amount"),
                "actual_amount": actual.get("approved_amount"),
                "confidence": actual.get("confidence_score"),
                "processing_time_ms": actual.get("processing_time_ms"),
            })

        except Exception as e:
            logger.error(f"Test case {case_id} failed: {e}")
            results.append({
                "case_id": case_id,
                "case_name": tc.get("case_name", ""),
                "correct": False,
                "error": str(e),
            })

    accuracy = correct / total if total > 0 else 0
    _last_evaluation_results = {
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "results": results,
    }
    return _last_evaluation_results
