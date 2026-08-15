from __future__ import annotations
import json
import os

_DEFAULT_DOCS: list[dict] = [
    {"id": "doc-1", "title": "Checkout Service Architecture",
     "content": "The checkout-api service handles the entire checkout flow. It communicates with payment-service, inventory-service, and user-service. The service uses a PostgreSQL database with a connection pool of 20 connections. Each checkout request opens a database transaction. The service is deployed as a Kubernetes deployment with 3 replicas."},
    {"id": "doc-2", "title": "Database Connection Pool Configuration",
     "content": "Database connection pool is configured with max_connections=20, timeout=5s, and retry_attempts=3. When all connections are in use, new requests queue up to 10s before timing out. The retry mechanism in checkout-v2.4 creates new connection attempts on failure, which can lead to connection pool exhaustion under high load."},
    {"id": "doc-3", "title": "Deployment Process",
     "content": "Deployments follow blue-green strategy. Each deployment is rolled out gradually: 10% traffic initially, then 50%, then 100% after 15 minutes of monitoring. Rollback can be triggered manually or via automated health check failure. All deployments require a signed commit and peer review."},
    {"id": "doc-4", "title": "Incident Response Runbook",
     "content": "Severity levels: critical (service down), major (degraded), minor (cosmetic). Critical incidents require immediate response with 15min SLA. Major incidents have 60min SLA. All incidents must be documented with root cause analysis within 24 hours of resolution."},
    {"id": "doc-5", "title": "Payment Service Documentation",
     "content": "payment-service handles payment processing via external payment gateway. Uses webhook callbacks for async payment confirmation. Webhook timeout is configured at 5s. The service maintains a retry queue for failed payments with exponential backoff."},
    {"id": "doc-6", "title": "Monitoring and Alerting",
     "content": "Prometheus metrics collected every 15s. Alert thresholds: p99 latency > 500ms triggers P1 alert, error rate > 2% triggers P2 alert, CPU > 80% triggers P3 alert. Alerts are routed to on-call SRE via PagerDuty."},
    {"id": "doc-7", "title": "Checkout v2.4 Release Notes",
     "content": "Version checkout-v2.4 introduces improved retry logic for database transactions. Key changes: Added retry_attempts=3 with 100ms backoff. Changed connection acquisition to block until timeout instead of failing fast. Known risk: under high concurrency, retry logic may compound connection pool pressure."},
    {"id": "doc-8", "title": "Historical Incident INC-104",
     "content": "INC-104: Database timeout after retry logic deployment. Checkout-v2.4 introduced retry logic causing cascading database timeouts. Each retry consumes a connection, leading to pool exhaustion. Symptoms: p99 latency spike from 120ms to 520ms, error rate increase from 0.5% to 4.2%, database timeout errors in logs. Resolution: Rollback checkout-v2.4 and increase connection pool to 50."},
]

CHUNK_SIZE = 300


def chunk_document(doc: dict) -> list[dict]:
    content = doc["content"]
    chunks = []
    words = content.split()
    for i in range(0, len(words), CHUNK_SIZE):
        chunk_text = " ".join(words[i:i + CHUNK_SIZE])
        chunks.append({
            "id": f"{doc['id']}-chunk-{i // CHUNK_SIZE}",
            "title": doc["title"],
            "content": chunk_text,
        })
    return chunks


def get_all_chunks() -> list[dict]:
    chunks = []
    for doc in _DEFAULT_DOCS:
        chunks.extend(chunk_document(doc))
    return chunks


def get_documents() -> list[dict]:
    return _DEFAULT_DOCS
