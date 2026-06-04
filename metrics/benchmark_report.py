"""Benchmark report generation."""

from metrics.accuracy import calculate_accuracy
from metrics.latency import analyze_latencies


def generate_report(eval_results: dict) -> str:
    """Generate a formatted benchmark report."""
    results = eval_results.get("results", [])
    accuracy = calculate_accuracy(results)
    latency = analyze_latencies(results)

    report = []
    report.append("=" * 60)
    report.append("  PLUM OPD CLAIM ADJUDICATOR - BENCHMARK REPORT")
    report.append("=" * 60)
    report.append(f"\nOverall Accuracy: {accuracy['accuracy']*100:.1f}% ({accuracy['correct']}/{accuracy['total']})")
    report.append(f"\nLatency: avg={latency['avg_ms']}ms, p95={latency.get('p95_ms', 'N/A')}ms")
    report.append(f"\nPer-class metrics:")

    for dt in ["APPROVED", "REJECTED", "PARTIAL", "MANUAL_REVIEW"]:
        p = accuracy["precision"].get(dt, 0)
        r = accuracy["recall"].get(dt, 0)
        f = accuracy["f1"].get(dt, 0)
        report.append(f"  {dt:15s} | P={p:.2f} | R={r:.2f} | F1={f:.2f}")

    report.append("\n" + "=" * 60)
    return "\n".join(report)
