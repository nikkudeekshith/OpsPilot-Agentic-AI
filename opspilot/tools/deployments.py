from __future__ import annotations
import time

_DEPLOY_DB: list[dict] = []


def seed_deployments():
    global _DEPLOY_DB
    now = time.time()
    _DEPLOY_DB = [
        {"service": "checkout-api", "version": "checkout-v2.3", "status": "stable",  "timestamp": now - 86400 * 7, "by": "alice"},
        {"service": "checkout-api", "version": "checkout-v2.4", "status": "active",  "timestamp": now - 5400, "by": "bob",
         "commit": "a1b2c3d", "description": "Added database retry logic for checkout flow"},
        {"service": "checkout-api", "version": "checkout-v2.4", "status": "rollback_pending", "timestamp": now - 5400, "by": "bob"},
        {"service": "payment-service", "version": "payment-v1.8", "status": "stable",  "timestamp": now - 86400 * 3, "by": "alice"},
        {"service": "payment-service", "version": "payment-v1.9", "status": "active",  "timestamp": now - 7200, "by": "charlie",
         "commit": "e4f5g6h", "description": "Updated payment webhook handling"},
        {"service": "payment-gateway", "version": "gw-v3.1", "status": "active",  "timestamp": now - 86400 * 14, "by": "alice"},
    ]


def get_deployments(service: str, limit: int = 10) -> dict:
    if not _DEPLOY_DB:
        seed_deployments()
    results = [d for d in _DEPLOY_DB if d["service"] == service]
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"service": service, "deployments": results[:limit]}
