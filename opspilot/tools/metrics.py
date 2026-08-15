from __future__ import annotations
import time
import random

_METRICS_DB: dict[str, list[dict]] = {}


def seed_metrics():
    now = time.time()
    _METRICS_DB.clear()
    base = [
        {"service": "checkout-api", "metric": "p99_latency_ms", "value": 120, "timestamp": now - 7200},
        {"service": "checkout-api", "metric": "p99_latency_ms", "value": 115, "timestamp": now - 6300},
        {"service": "checkout-api", "metric": "p99_latency_ms", "value": 118, "timestamp": now - 5400},
        {"service": "checkout-api", "metric": "p99_latency_ms", "value": 480, "timestamp": now - 4500},
        {"service": "checkout-api", "metric": "p99_latency_ms", "value": 510, "timestamp": now - 3600},
        {"service": "checkout-api", "metric": "p99_latency_ms", "value": 495, "timestamp": now - 2700},
        {"service": "checkout-api", "metric": "p99_latency_ms", "value": 520, "timestamp": now - 1800},
        {"service": "checkout-api", "metric": "p99_latency_ms", "value": 505, "timestamp": now - 900},
        {"service": "checkout-api", "metric": "p99_latency_ms", "value": 530, "timestamp": now},
        {"service": "checkout-api", "metric": "error_rate_pct", "value": 0.5, "timestamp": now - 7200},
        {"service": "checkout-api", "metric": "error_rate_pct", "value": 0.6, "timestamp": now - 5400},
        {"service": "checkout-api", "metric": "error_rate_pct", "value": 3.2, "timestamp": now - 4500},
        {"service": "checkout-api", "metric": "error_rate_pct", "value": 3.8, "timestamp": now - 3600},
        {"service": "checkout-api", "metric": "error_rate_pct", "value": 4.1, "timestamp": now - 2700},
        {"service": "checkout-api", "metric": "error_rate_pct", "value": 3.9, "timestamp": now - 1800},
        {"service": "checkout-api", "metric": "error_rate_pct", "value": 4.2, "timestamp": now - 900},
        {"service": "checkout-api", "metric": "error_rate_pct", "value": 4.0, "timestamp": now},
        {"service": "checkout-api", "metric": "cpu_utilization_pct", "value": 35, "timestamp": now - 7200},
        {"service": "checkout-api", "metric": "cpu_utilization_pct", "value": 38, "timestamp": now - 5400},
        {"service": "checkout-api", "metric": "cpu_utilization_pct", "value": 72, "timestamp": now - 4500},
        {"service": "checkout-api", "metric": "cpu_utilization_pct", "value": 78, "timestamp": now - 3600},
        {"service": "checkout-api", "metric": "cpu_utilization_pct", "value": 75, "timestamp": now - 2700},
        {"service": "checkout-api", "metric": "cpu_utilization_pct", "value": 80, "timestamp": now - 1800},
        {"service": "checkout-api", "metric": "cpu_utilization_pct", "value": 76, "timestamp": now - 900},
        {"service": "checkout-api", "metric": "cpu_utilization_pct", "value": 82, "timestamp": now},
        {"service": "payment-service", "metric": "p99_latency_ms", "value": 80, "timestamp": now - 7200},
        {"service": "payment-service", "metric": "p99_latency_ms", "value": 350, "timestamp": now - 4500},
        {"service": "payment-service", "metric": "p99_latency_ms", "value": 340, "timestamp": now - 3600},
        {"service": "payment-service", "metric": "p99_latency_ms", "value": 360, "timestamp": now - 1800},
        {"service": "checkout-api", "metric": "memory_usage_mb", "value": 256, "timestamp": now - 7200},
        {"service": "checkout-api", "metric": "memory_usage_mb", "value": 512, "timestamp": now - 4500},
        {"service": "checkout-api", "metric": "memory_usage_mb", "value": 540, "timestamp": now - 2700},
        {"service": "checkout-api", "metric": "memory_usage_mb", "value": 530, "timestamp": now - 900},
    ]
    for entry in base:
        _METRICS_DB.setdefault(entry["service"], []).append(entry)


def query_metrics(service: str, metric_name: str, start_time: float | None = None, end_time: float | None = None) -> dict:
    if not _METRICS_DB:
        seed_metrics()
    entries = _METRICS_DB.get(service, [])
    filtered = [e for e in entries if e["metric"] == metric_name]
    if start_time:
        filtered = [e for e in filtered if e["timestamp"] >= start_time]
    if end_time:
        filtered = [e for e in filtered if e["timestamp"] <= end_time]
    values = [e["value"] for e in filtered]
    if not values:
        return {"service": service, "metric": metric_name, "data": [], "summary": "No data found"}
    return {
        "service": service,
        "metric": metric_name,
        "data": filtered,
        "summary": {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1] if values else None,
            "count": len(values),
        },
    }
