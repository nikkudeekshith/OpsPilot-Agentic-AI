from __future__ import annotations
from typing import Any, Callable
from opspilot.schemas import ToolSpec, ToolResult, ToolCategory
from opspilot.tools.metrics import query_metrics
from opspilot.tools.logs import search_logs
from opspilot.tools.deployments import get_deployments
from opspilot.tools.incidents import search_incidents
from opspilot.tools.runbook import retrieve_runbook
from opspilot.tools.report import create_incident_report
from opspilot.tools.rollback import request_rollback


ToolFunc = Callable[..., Any]

_DEFAULT_TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="query_metrics",
        description="Query time-series metrics for a service (latency, error rate, CPU, memory)",
        parameters={
            "service": {"type": "string", "description": "Service name (e.g. checkout-api)"},
            "metric_name": {"type": "string", "description": "Metric name (e.g. p99_latency_ms, error_rate_pct)"},
            "start_time": {"type": "number", "description": "Start timestamp (epoch seconds)", "required": False},
            "end_time": {"type": "number", "description": "End timestamp (epoch seconds)", "required": False},
        },
        category=ToolCategory.READ,
    ),
    ToolSpec(
        name="search_logs",
        description="Search logs for a service with optional level and keyword filters",
        parameters={
            "service": {"type": "string", "description": "Service name"},
            "level": {"type": "string", "description": "Log level (INFO, WARN, ERROR)", "required": False},
            "keywords": {"type": "string", "description": "Keywords to search in log messages", "required": False},
            "start_time": {"type": "number", "description": "Start timestamp", "required": False},
            "end_time": {"type": "number", "description": "End timestamp", "required": False},
            "limit": {"type": "integer", "description": "Max results", "required": False},
        },
        category=ToolCategory.READ,
    ),
    ToolSpec(
        name="get_deployments",
        description="Get deployment history for a service",
        parameters={
            "service": {"type": "string", "description": "Service name"},
            "limit": {"type": "integer", "description": "Max results", "required": False},
        },
        category=ToolCategory.READ,
    ),
    ToolSpec(
        name="search_incidents",
        description="Search historical incidents by service or keywords",
        parameters={
            "service": {"type": "string", "description": "Service name", "required": False},
            "keywords": {"type": "string", "description": "Keywords to search", "required": False},
            "limit": {"type": "integer", "description": "Max results", "required": False},
        },
        category=ToolCategory.READ,
    ),
    ToolSpec(
        name="retrieve_runbook",
        description="Retrieve runbook documentation for a given topic",
        parameters={
            "query": {"type": "string", "description": "Search query for runbook topic"},
        },
        category=ToolCategory.READ,
    ),
    ToolSpec(
        name="create_incident_report",
        description="Create a final incident report with root cause, evidence, and recommendations",
        parameters={
            "incident_id": {"type": "string", "description": "Incident ID"},
            "root_cause": {"type": "string", "description": "Identified root cause"},
            "confidence": {"type": "number", "description": "Confidence score 0-1"},
            "evidence": {"type": "array", "description": "List of evidence strings",
                         "items": {"type": "string"}},
            "recommended_action": {"type": "string", "description": "Recommended action"},
            "requires_approval": {"type": "boolean", "description": "Whether action needs approval"},
        },
        category=ToolCategory.WRITE,
    ),
    ToolSpec(
        name="request_rollback",
        description="Request a rollback of a service deployment. Requires human approval.",
        parameters={
            "service": {"type": "string", "description": "Service name"},
            "version": {"type": "string", "description": "Version to rollback"},
            "reason": {"type": "string", "description": "Reason for rollback"},
            "evidence_summary": {"type": "string", "description": "Summary of evidence"},
        },
        category=ToolCategory.APPROVAL,
        required_approval=True,
    ),
]


class ToolRegistry:
    def __init__(self):
        self._specs: dict[str, ToolSpec] = {}
        self._fns: dict[str, ToolFunc] = {}
        self._register_defaults()

    def _register_defaults(self):
        implementations: dict[str, ToolFunc] = {
            "query_metrics": query_metrics,
            "search_logs": search_logs,
            "get_deployments": get_deployments,
            "search_incidents": search_incidents,
            "retrieve_runbook": retrieve_runbook,
            "create_incident_report": create_incident_report,
            "request_rollback": request_rollback,
        }
        for spec in _DEFAULT_TOOLS:
            self._specs[spec.name] = spec
            if spec.name in implementations:
                self._fns[spec.name] = implementations[spec.name]

    def register(self, spec: ToolSpec, fn: ToolFunc):
        self._specs[spec.name] = spec
        self._fns[spec.name] = fn

    def get_spec(self, name: str) -> ToolSpec | None:
        return self._specs.get(name)

    def get_fn(self, name: str) -> ToolFunc | None:
        return self._fns.get(name)

    def list_tools(self) -> list[ToolSpec]:
        return list(self._specs.values())

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        fn = self._fns.get(name)
        spec = self._specs.get(name)
        if not fn or not spec:
            return ToolResult(tool=name, arguments=arguments, success=False, error=f"Tool '{name}' not found")
        try:
            result = fn(**arguments)
            return ToolResult(tool=name, arguments=arguments, observation=result, success=True)
        except Exception as e:
            return ToolResult(tool=name, arguments=arguments, success=False, error=str(e))
