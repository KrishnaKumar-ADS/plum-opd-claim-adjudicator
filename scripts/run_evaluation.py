"""Run benchmark evaluation suite."""

import sys
import os
import json

# Ensure stdout and stderr use UTF-8 encoding on Windows to prevent UnicodeEncodeError
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.evaluation_service import run_evaluation


def main():
    print("Running evaluation suite...")
    print("=" * 60)

    results = run_evaluation()

    print(f"\nResults: {results['correct']}/{results['total']} correct")
    print(f"Accuracy: {results['accuracy'] * 100:.1f}%")
    print("=" * 60)

    # Save results first before any potential printing issues
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "evaluations", "eval_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")

    # Print results safely
    for r in results["results"]:
        status = "OK" if r.get("correct") else "FAIL"
        try:
            print(f"  [{status}] {r['case_id']}: expected={r.get('expected_decision')}, actual={r.get('actual_decision')}")
            if not r.get("correct"):
                print(f"     Expected Amt: {r.get('expected_amount')}, Actual Amt: {r.get('actual_amount')}")
                if r.get("error"):
                    print(f"     Error: {r['error']}")
        except Exception as e:
            print(f"  [{status}] {r['case_id']}: encoding/print error {str(e)}")


if __name__ == "__main__":
    main()

