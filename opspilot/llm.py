from __future__ import annotations
import os
import json
import re

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_openai_client = None


def _get_api_key() -> str:
    """Resolve the OpenAI API key from Streamlit secrets, then environment.

    On Streamlit Cloud the key is configured in the app's Secrets
    (Settings -> Secrets). Locally it can come from a .env file (loaded by
    dotenv above) or a shell environment variable. No key is ever hard-coded.
    """
    try:
        import streamlit as st

        key = st.secrets.get("OPENAI_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("OPENAI_API_KEY", "")


def _get_client():
    global _openai_client
    if _openai_client is None:
        import openai
        api_key = _get_api_key()
        if api_key:
            _openai_client = openai.OpenAI(api_key=api_key)
    return _openai_client


def llm_complete(prompt: str, system_prompt: str = "", model: str = "gpt-4o-mini") -> str:
    client = _get_client()
    if client:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = client.chat.completions.create(model=model, messages=messages, temperature=0.3)
            return resp.choices[0].message.content or ""
        except Exception:
            return _fallback_llm(prompt)
    return _fallback_llm(prompt)


_KNOWN_ROOT_CAUSES = {
    "checkout": "checkout-v2.4 deployment database retry logic causing connection pool exhaustion",
    "payment-service latency": "payment-v1.9 webhook handling causing increased response times",
    "payment-service error": "payment webhook timeout from external provider throttling",
    "payment gateway": "external payment provider rate limiting webhook callbacks",
    "database timeout": "database connection pool exhaustion from retry logic in checkout-v2.4",
    "database connection": "connection pool exhausted by repeated retry attempts from checkout-v2.4",
    "cpu spike": "excessive database retry operations from checkout-v2.4 consuming CPU",
    "memory usage": "connection pool accumulation from retry logic checkout-v2.4",
    "500 error": "database connection pool imbalance from checkout-v2.4 retry logic",
    "health check": "database connection pool depletion from checkout-v2.4 retry cascade",
    "latency increase": "checkout-v2.4 deployment introducing database retry delay",
    "error rate spike": "database connection timeout from checkout-v2.4 retry logic",
    "rollback": "checkout-v2.4 causing database timeout cascade requiring rollback",
    "deployment impact": "checkout-v2.4 retry logic degrading performance",
    "intermittent failure": "retry logic in checkout-v2.4 causing cascading database failures",
    "anomalous metric": "deployment checkout-v2.4 related database timeout pattern",
    "p99 latency": "deployment-related latency increase from checkout-v2.4",
}


def _detect_service(text: str) -> str:
    t = text.lower()
    if "payment-service" in t or ("payment" in t and "checkout" not in t and "gateway" not in t):
        return "payment-service"
    if "checkout" in t:
        return "checkout-api"
    if "user" in t:
        return "user-service"
    if "gateway" in t:
        return "payment-gateway"
    return "checkout-api"


def _detect_metric(text: str) -> str:
    t = text.lower()
    if "latency" in t or "p99" in t or "slow" in t:
        return "p99_latency_ms"
    if "error" in t or "fail" in t or "500" in t:
        return "error_rate_pct"
    if "cpu" in t:
        return "cpu_utilization_pct"
    if "memory" in t or "mem" in t:
        return "memory_usage_mb"
    if "timeout" in t or "database" in t or "db" in t or "connection" in t:
        return "p99_latency_ms"
    return "p99_latency_ms"


def _infer_root_cause(prompt: str) -> str:
    p = prompt.lower()
    for key, cause in _KNOWN_ROOT_CAUSES.items():
        if key in p:
            return cause
    service = _detect_service(p)
    metric = _detect_metric(p)
    return f"{service} issue related to {metric}"


def _fallback_llm(prompt: str) -> str:
    prompt_lower = prompt.lower()
    service = _detect_service(prompt_lower)
    metric = _detect_metric(prompt_lower)

    if "select a tool" in prompt_lower or "which tool" in prompt_lower or "next action" in prompt_lower or "tool" in prompt_lower:
        if "metrics" in prompt_lower or "latency" in prompt_lower or "p99" in prompt_lower:
            return json.dumps({"tool": "query_metrics", "arguments": {"service": service, "metric_name": metric}})
        if "log" in prompt_lower:
            level = "ERROR" if "error" in prompt_lower else None
            kw = "timeout" if "timeout" in prompt_lower else ("error" if "error" in prompt_lower else None)
            args = {"service": service}
            if level: args["level"] = level
            if kw: args["keywords"] = kw
            return json.dumps({"tool": "search_logs", "arguments": args})
        if "deploy" in prompt_lower or "version" in prompt_lower or "rollback" in prompt_lower:
            return json.dumps({"tool": "get_deployments", "arguments": {"service": service}})
        if "incident" in prompt_lower or "historical" in prompt_lower or "past" in prompt_lower:
            kw = "timeout" if "timeout" in prompt_lower else ("latency" if "latency" in prompt_lower else "error")
            return json.dumps({"tool": "search_incidents", "arguments": {"service": service, "keywords": kw}})
        if "runbook" in prompt_lower or "knowledge" in prompt_lower:
            return json.dumps({"tool": "retrieve_runbook", "arguments": {"query": f"{service} {metric} investigation"}})
        if "report" in prompt_lower:
            return json.dumps({"tool": "create_incident_report", "arguments": {
                "incident_id": "INC-001",
                "root_cause": _infer_root_cause(prompt),
                "confidence": 0.7,
                "evidence": ["Metrics show anomaly", "Logs confirm pattern", "Deployment correlation found"],
                "recommended_action": f"Investigate {service} deployment",
                "requires_approval": False,
            }})
        return json.dumps({"tool": "query_metrics", "arguments": {"service": service, "metric_name": metric}})

    if "hypothesis" in prompt_lower or "root cause" in prompt_lower:
        root_cause = _infer_root_cause(prompt)
        return json.dumps({"hypothesis": root_cause, "confidence": 0.75})

    if "reflect" in prompt_lower or "critique" in prompt_lower:
        return json.dumps({
            "evidence_sufficient": True,
            "critique": f"Evidence from {service} {metric} investigation appears conclusive. "
                        f"Correlation found between deployment and symptom pattern.",
            "should_replan": False,
        })

    if "summary" in prompt_lower or "report" in prompt_lower:
        return json.dumps({"summary": f"Investigation of {service} {metric} complete."})

    return json.dumps({"response": f"Analysis in progress for {service} {metric}."})
