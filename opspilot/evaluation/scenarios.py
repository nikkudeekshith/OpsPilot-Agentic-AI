from __future__ import annotations

SCENARIOS = [
    {"id": "S001", "goal": "Investigate why checkout API latency increased in the last two hours", "expected_tools": ["query_metrics", "search_logs", "get_deployments", "search_incidents", "retrieve_runbook"], "expected_root_cause": "checkout-v2.4 deployment database retry logic", "expected_confidence_min": 0.7},
    {"id": "S002", "goal": "Investigate error rate spike on checkout-api", "expected_tools": ["query_metrics", "search_logs", "get_deployments", "search_incidents"], "expected_root_cause": "database connection timeout", "expected_confidence_min": 0.6},
    {"id": "S003", "goal": "Investigate database timeout errors on checkout-api", "expected_tools": ["query_metrics", "search_logs", "get_deployments", "search_incidents", "retrieve_runbook"], "expected_root_cause": "database connection pool exhaustion from retry logic", "expected_confidence_min": 0.7},
    {"id": "S004", "goal": "Check why payment-service is returning high latency", "expected_tools": ["query_metrics", "search_logs", "get_deployments"], "expected_root_cause": "payment-v1.9 webhook handling", "expected_confidence_min": 0.5},
    {"id": "S005", "goal": "Investigate CPU spike on checkout-api", "expected_tools": ["query_metrics", "search_logs", "get_deployments"], "expected_root_cause": "increased database retry activity", "expected_confidence_min": 0.5},
    {"id": "S006", "goal": "Investigate memory usage increase on checkout-api", "expected_tools": ["query_metrics", "search_logs", "get_deployments", "search_incidents"], "expected_root_cause": "connection pool exhaustion", "expected_confidence_min": 0.5},
    {"id": "S007", "goal": "Investigate why payment gateway callbacks are slow", "expected_tools": ["query_metrics", "search_logs", "retrieve_runbook"], "expected_root_cause": "external provider throttling", "expected_confidence_min": 0.4},
    {"id": "S008", "goal": "Investigate checkout-api 500 errors during peak hours", "expected_tools": ["query_metrics", "search_logs", "get_deployments", "search_incidents"], "expected_root_cause": "database connection pool imbalance", "expected_confidence_min": 0.5},
    {"id": "S009", "goal": "Investigate intermittent checkout failures", "expected_tools": ["search_logs", "query_metrics", "get_deployments"], "expected_root_cause": "retry logic causing cascading failures", "expected_confidence_min": 0.5},
    {"id": "S010", "goal": "Investigate recent deployment impact on checkout-api", "expected_tools": ["get_deployments", "query_metrics", "search_logs", "search_incidents"], "expected_root_cause": "checkout-v2.4 retry logic", "expected_confidence_min": 0.7},
    {"id": "S011", "goal": "Investigate if checkout latency is related to database issues", "expected_tools": ["query_metrics", "search_logs", "retrieve_runbook", "search_incidents"], "expected_root_cause": "database timeout from connection pool exhaustion", "expected_confidence_min": 0.6},
    {"id": "S012", "goal": "Investigate payment-webhook timeout errors", "expected_tools": ["search_logs", "query_metrics", "get_deployments", "retrieve_runbook"], "expected_root_cause": "payment-v1.9 webhook timeout handling", "expected_confidence_min": 0.5},
    {"id": "S013", "goal": "Investigate if recent changes caused checkout degradation", "expected_tools": ["get_deployments", "query_metrics", "search_logs", "search_incidents"], "expected_root_cause": "checkout-v2.4 retry logic causing pool exhaustion", "expected_confidence_min": 0.7},
    {"id": "S014", "goal": "Investigate error rate on payment-service", "expected_tools": ["query_metrics", "search_logs", "get_deployments", "search_incidents"], "expected_root_cause": "payment webhook timeout", "expected_confidence_min": 0.5},
    {"id": "S015", "goal": "Investigate why database connections are timing out", "expected_tools": ["search_logs", "query_metrics", "get_deployments", "retrieve_runbook", "search_incidents"], "expected_root_cause": "connection pool exhausted by retry logic", "expected_confidence_min": 0.7},
    {"id": "S016", "goal": "Investigate p99 latency trend on checkout-api", "expected_tools": ["query_metrics", "search_logs", "get_deployments"], "expected_root_cause": "deployment-related latency increase", "expected_confidence_min": 0.6},
    {"id": "S017", "goal": "Investigate if checkout-api has memory leak", "expected_tools": ["query_metrics", "search_logs", "get_deployments", "search_incidents"], "expected_root_cause": "connection pool accumulation from retries", "expected_confidence_min": 0.4},
    {"id": "S018", "goal": "Investigate high CPU on checkout-api during checkout flow", "expected_tools": ["query_metrics", "search_logs", "get_deployments"], "expected_root_cause": "excessive database retry operations", "expected_confidence_min": 0.5},
    {"id": "S019", "goal": "Investigate checkout-api failing health checks", "expected_tools": ["search_logs", "query_metrics", "get_deployments", "search_incidents"], "expected_root_cause": "database connection pool depletion", "expected_confidence_min": 0.6},
    {"id": "S020", "goal": "Investigate relationship between deployment and errors", "expected_tools": ["get_deployments", "query_metrics", "search_logs", "search_incidents"], "expected_root_cause": "checkout-v2.4 introducing retry-related errors", "expected_confidence_min": 0.7},
    {"id": "S021", "goal": "Investigate checkout-api timeouts after v2.4 deploy", "expected_tools": ["get_deployments", "query_metrics", "search_logs", "search_incidents", "retrieve_runbook"], "expected_root_cause": "checkout-v2.4 retry logic causing database timeout cascade", "expected_confidence_min": 0.8},
    {"id": "S022", "goal": "Investigate impact of database pool on checkout latency", "expected_tools": ["query_metrics", "search_logs", "retrieve_runbook", "search_incidents"], "expected_root_cause": "connection pool exhaustion from retry attempts", "expected_confidence_min": 0.6},
    {"id": "S023", "goal": "Investigate if checkout errors are from payment upstream", "expected_tools": ["query_metrics", "search_logs", "search_incidents", "retrieve_runbook"], "expected_root_cause": "payment gateway callback latency", "expected_confidence_min": 0.4},
    {"id": "S024", "goal": "Investigate sudden increase in checkout-api traffic errors", "expected_tools": ["query_metrics", "search_logs", "get_deployments", "search_incidents"], "expected_root_cause": "deployment checkout-v2.4 retry logic failure", "expected_confidence_min": 0.6},
    {"id": "S025", "goal": "Investigate whether rollback is needed for checkout-api", "expected_tools": ["get_deployments", "query_metrics", "search_logs", "search_incidents"], "expected_root_cause": "checkout-v2.4 causing database timeout cascade", "expected_confidence_min": 0.7},
    {"id": "S026", "goal": "Investigate database retry logic effects on checkout performance", "expected_tools": ["query_metrics", "search_logs", "retrieve_runbook", "get_deployments", "search_incidents"], "expected_root_cause": "retry loop consuming all database connections", "expected_confidence_min": 0.7},
    {"id": "S027", "goal": "Investigate if checkout-v2.4 should be rolled back", "expected_tools": ["get_deployments", "query_metrics", "search_logs", "search_incidents", "retrieve_runbook"], "expected_root_cause": "checkout-v2.4 retry logic causing database pool exhaustion", "expected_confidence_min": 0.8},
    {"id": "S028", "goal": "Investigate anomalous metrics on checkout-api", "expected_tools": ["query_metrics", "search_logs", "get_deployments", "search_incidents"], "expected_root_cause": "deployment-related database timeout", "expected_confidence_min": 0.5},
    {"id": "S029", "goal": "Investigate correlation between deployment time and error rate", "expected_tools": ["get_deployments", "query_metrics", "search_logs"], "expected_root_cause": "deployment checkout-v2.4 causing error spike", "expected_confidence_min": 0.6},
    {"id": "S030", "goal": "Investigate full incident lifecycle for checkout database timeout", "expected_tools": ["query_metrics", "search_logs", "get_deployments", "search_incidents", "retrieve_runbook"], "expected_root_cause": "database connection pool exhaustion from retry logic in checkout-v2.4", "expected_confidence_min": 0.8},
]


def get_scenario(scenario_id: str) -> dict | None:
    for s in SCENARIOS:
        if s["id"] == scenario_id:
            return s
    return None


def get_all_scenarios() -> list[dict]:
    return SCENARIOS
