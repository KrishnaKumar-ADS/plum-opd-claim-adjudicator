"""Latency tracking per adjudication step."""

import time
from contextlib import contextmanager


class LatencyTracker:
    """Track latency of adjudication pipeline steps."""

    def __init__(self):
        self.timings = {}

    @contextmanager
    def track(self, step_name: str):
        start = time.time()
        yield
        elapsed = (time.time() - start) * 1000
        self.timings[step_name] = round(elapsed, 2)

    def get_report(self) -> dict:
        total = sum(self.timings.values())
        return {
            "steps": self.timings,
            "total_ms": round(total, 2),
            "bottleneck": max(self.timings, key=self.timings.get) if self.timings else None,
        }


def analyze_latencies(results: list[dict]) -> dict:
    """Analyze latency across multiple evaluation results."""
    times = [r.get("processing_time_ms", 0) for r in results if r.get("processing_time_ms")]
    if not times:
        return {"avg_ms": 0, "min_ms": 0, "max_ms": 0, "p95_ms": 0}

    times.sort()
    p95_idx = int(len(times) * 0.95)
    return {
        "avg_ms": round(sum(times) / len(times), 0),
        "min_ms": min(times),
        "max_ms": max(times),
        "p95_ms": times[min(p95_idx, len(times) - 1)],
        "count": len(times),
    }
