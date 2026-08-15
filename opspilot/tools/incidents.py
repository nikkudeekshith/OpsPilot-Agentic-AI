from __future__ import annotations
import time

_INCIDENT_DB: list[dict] = []


def seed_incidents():
    global _INCIDENT_DB
    now = time.time()
    _INCIDENT_DB = [
        {"id": "INC-101", "service": "checkout-api", "title": "Checkout latency spike after deployment",
         "summary": "P99 latency increased 4x after checkout-v2.2 deployment. Root cause: database connection pool exhaustion.",
         "status": "resolved", "severity": "critical", "timestamp": now - 86400 * 14,
         "root_cause": "Database connection pool too small for peak traffic"},
        {"id": "INC-102", "service": "payment-service", "title": "Payment failures due to webhook timeout",
         "summary": "Payment webhook responses timing out after 5s. Root cause: external provider throttling.",
         "status": "resolved", "severity": "major", "timestamp": now - 86400 * 7,
         "root_cause": "External payment provider rate limiting"},
        {"id": "INC-103", "service": "checkout-api", "title": "Intermittent 500 errors on checkout",
         "summary": "Random 500 errors during peak hours. Root cause: memory leak in session handler.",
         "status": "resolved", "severity": "critical", "timestamp": now - 86400 * 3,
         "root_cause": "Memory leak in session handler"},
        {"id": "INC-104", "service": "checkout-api", "title": "Database timeout after retry logic deployment",
         "summary": "Checkout-v2.4 introduced retry logic causing cascading database timeouts. Each retry consumes a connection, leading to pool exhaustion.",
         "status": "investigating", "severity": "critical", "timestamp": now - 3600,
         "root_cause": "Retry logic in checkout-v2.4 exhausting database connection pool"},
        {"id": "INC-105", "service": "user-service", "title": "User auth latency",
         "summary": "User authentication taking >2s. Root cause: Redis cache miss storm.",
         "status": "resolved", "severity": "minor", "timestamp": now - 86400 * 30,
         "root_cause": "Redis cache miss storm"},
    ]


def search_incidents(service: str | None = None, keywords: str | None = None, limit: int = 10) -> dict:
    if not _INCIDENT_DB:
        seed_incidents()
    results = list(_INCIDENT_DB)
    if service:
        results = [i for i in results if i["service"] == service]
    if keywords:
        kw = keywords.lower()
        results = [i for i in results if kw in i["title"].lower() or kw in i["summary"].lower() or kw in i.get("root_cause", "").lower()]
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"incidents": results[:limit], "total_matches": len(results)}
