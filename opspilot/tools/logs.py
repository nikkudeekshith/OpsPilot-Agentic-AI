from __future__ import annotations
import time

_LOG_DB: list[dict] = []


def seed_logs():
    global _LOG_DB
    now = time.time()
    _LOG_DB = [
        {"service": "checkout-api", "level": "INFO",  "message": "Request completed in 120ms", "timestamp": now - 7200, "trace_id": "abc123"},
        {"service": "checkout-api", "level": "INFO",  "message": "Request completed in 115ms", "timestamp": now - 6300, "trace_id": "abc124"},
        {"service": "checkout-api", "level": "WARN",  "message": "Database query slow: 950ms", "timestamp": now - 4600, "trace_id": "abc125"},
        {"service": "checkout-api", "level": "ERROR", "message": "Database connection timeout after 5s", "timestamp": now - 4500, "trace_id": "abc126"},
        {"service": "checkout-api", "level": "ERROR", "message": "Database connection timeout after 5s", "timestamp": now - 4450, "trace_id": "abc127"},
        {"service": "checkout-api", "level": "ERROR", "message": "Retry attempt 1/3 failed", "timestamp": now - 4400, "trace_id": "abc127"},
        {"service": "checkout-api", "level": "ERROR", "message": "Retry attempt 2/3 failed", "timestamp": now - 4350, "trace_id": "abc127"},
        {"service": "checkout-api", "level": "ERROR", "message": "Retry attempt 3/3 failed - giving up", "timestamp": now - 4300, "trace_id": "abc127"},
        {"service": "checkout-api", "level": "ERROR", "message": "Database connection timeout after 5s", "timestamp": now - 3600, "trace_id": "abc128"},
        {"service": "checkout-api", "level": "ERROR", "message": "Database connection timeout after 5s", "timestamp": now - 2700, "trace_id": "abc129"},
        {"service": "checkout-api", "level": "WARN",  "message": "Database query slow: 1200ms", "timestamp": now - 2650, "trace_id": "abc129"},
        {"service": "checkout-api", "level": "ERROR", "message": "Database connection timeout after 5s", "timestamp": now - 1800, "trace_id": "abc130"},
        {"service": "checkout-api", "level": "ERROR", "message": "Database connection timeout after 5s", "timestamp": now - 900,  "trace_id": "abc131"},
        {"service": "payment-service", "level": "INFO",  "message": "Payment processed successfully", "timestamp": now - 7200, "trace_id": "pay001"},
        {"service": "payment-service", "level": "INFO",  "message": "Payment processed successfully", "timestamp": now - 4500, "trace_id": "pay002"},
        {"service": "payment-service", "level": "WARN",  "message": "High callback latency: 800ms", "timestamp": now - 4400, "trace_id": "pay003"},
        {"service": "payment-gateway", "level": "INFO",  "message": "External provider response 200 OK", "timestamp": now - 7200, "trace_id": "gw001"},
        {"service": "payment-gateway", "level": "INFO",  "message": "External provider response 200 OK", "timestamp": now - 4500, "trace_id": "gw002"},
    ]


def search_logs(service: str, level: str | None = None, keywords: str | None = None,
                start_time: float | None = None, end_time: float | None = None,
                limit: int = 50) -> dict:
    if not _LOG_DB:
        seed_logs()
    results = [e for e in _LOG_DB if e["service"] == service]
    if level:
        results = [e for e in results if e["level"] == level.upper()]
    if keywords:
        kw = keywords.lower()
        results = [e for e in results if kw in e["message"].lower()]
    if start_time:
        results = [e for e in results if e["timestamp"] >= start_time]
    if end_time:
        results = [e for e in results if e["timestamp"] <= end_time]
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"service": service, "total_matches": len(results), "logs": results[:limit]}
