"""Accuracy metrics for adjudication decisions."""


def calculate_accuracy(results: list[dict]) -> dict:
    """Calculate accuracy metrics from evaluation results."""
    total = len(results)
    if total == 0:
        return {"accuracy": 0, "precision": {}, "recall": {}}

    correct = sum(1 for r in results if r.get("correct"))
    decision_types = ["APPROVED", "REJECTED", "PARTIAL", "MANUAL_REVIEW"]

    precision = {}
    recall = {}
    f1 = {}

    for dt in decision_types:
        tp = sum(1 for r in results if r.get("actual_decision") == dt and r.get("expected_decision") == dt)
        fp = sum(1 for r in results if r.get("actual_decision") == dt and r.get("expected_decision") != dt)
        fn = sum(1 for r in results if r.get("actual_decision") != dt and r.get("expected_decision") == dt)

        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        f = 2 * p * r / (p + r) if (p + r) > 0 else 0

        precision[dt] = round(p, 4)
        recall[dt] = round(r, 4)
        f1[dt] = round(f, 4)

    return {
        "accuracy": round(correct / total, 4),
        "total": total,
        "correct": correct,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
