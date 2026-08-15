from __future__ import annotations

_RUNBOOK_DB: dict[str, str] = {
    "checkout-latency": (
        "## Checkout Latency Investigation\n"
        "1. Check p99 latency metrics for checkout-api\n"
        "2. Search for ERROR/WARN logs in checkout-api (last 2 hours)\n"
        "3. Review recent deployments for checkout-api\n"
        "4. Check database connection pool metrics\n"
        "5. Search for similar historical incidents\n"
        "6. If latency > 500ms, check CPU/memory utilization\n"
        "7. If retry errors found, review retry logic configuration\n"
        "8. Escalate to SRE if database pool exhausted"
    ),
    "database-timeout": (
        "## Database Timeout Investigation\n"
        "1. Check database connection pool status\n"
        "2. Review slow query logs\n"
        "3. Check for recent deployments that may affect queries\n"
        "4. Review application retry configuration\n"
        "5. Check if connection pool size needs adjustment\n"
        "6. Consider rolling back recent deployment if correlated"
    ),
    "payment-failure": (
        "## Payment Failure Investigation\n"
        "1. Check payment-service error logs\n"
        "2. Verify payment-gateway external provider status\n"
        "3. Check webhook callback latency metrics\n"
        "4. Review recent payment-service deployments\n"
        "5. Check for upstream provider incidents"
    ),
    "incident-response": (
        "## General Incident Response\n"
        "1. Identify affected service and severity\n"
        "2. Check metrics for anomalies (latency, error rate, CPU)\n"
        "3. Search logs for ERROR/WARN patterns\n"
        "4. Review recent deployments\n"
        "5. Search for similar past incidents\n"
        "6. Form hypothesis based on evidence\n"
        "7. Verify hypothesis with additional data\n"
        "8. If confidence > 80%, propose action\n"
        "9. For rollback/restart actions, require human approval"
    ),
}


def retrieve_runbook(query: str) -> dict:
    query_lower = query.lower()
    candidates = []
    for key, content in _RUNBOOK_DB.items():
        if query_lower in key.replace("-", " ") or query_lower in content.lower():
            candidates.append({"key": key, "content": content, "relevance": 1.0})
    if not candidates:
        return {"query": query, "results": [], "message": "No matching runbook found"}
    return {"query": query, "results": candidates}
