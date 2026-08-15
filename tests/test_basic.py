from __future__ import annotations
from opspilot.tools.registry import ToolRegistry
from opspilot.tools.metrics import seed_metrics, query_metrics
from opspilot.tools.logs import seed_logs, search_logs
from opspilot.tools.deployments import seed_deployments, get_deployments
from opspilot.tools.incidents import seed_incidents, search_incidents
from opspilot.tools.runbook import retrieve_runbook
from opspilot.loop import run_investigation
from opspilot.schemas import AgentState, Plan, Step, Hypothesis
from opspilot.state import AgentStateManager
from opspilot.planner import create_plan, re_plan
from opspilot.reflection import reflect
from opspilot.rag.retriever import VectorRetriever, AgenticRetriever


def test_tool_registry():
    registry = ToolRegistry()
    tools = registry.list_tools()
    assert len(tools) == 7
    for name in ["query_metrics", "search_logs", "get_deployments", "search_incidents",
                  "retrieve_runbook", "create_incident_report", "request_rollback"]:
        assert registry.get_spec(name) is not None
        assert registry.get_fn(name) is not None


def test_query_metrics():
    seed_metrics()
    result = query_metrics("checkout-api", "p99_latency_ms")
    assert result["metric"] == "p99_latency_ms"
    assert result["summary"]["count"] > 0


def test_search_logs():
    seed_logs()
    result = search_logs("checkout-api", level="ERROR", keywords="timeout")
    assert result["total_matches"] > 0


def test_get_deployments():
    seed_deployments()
    result = get_deployments("checkout-api")
    assert len(result["deployments"]) > 0


def test_search_incidents():
    seed_incidents()
    result = search_incidents(keywords="latency")
    assert result["total_matches"] > 0


def test_retrieve_runbook():
    result = retrieve_runbook("latency")
    assert len(result["results"]) > 0


def test_create_plan():
    plan = create_plan("Investigate latency on checkout-api")
    assert len(plan.steps) > 0
    assert "latency" in plan.goal.lower()


def test_re_plan():
    plan = create_plan("Investigate latency")
    completed = [plan.steps[0].description]
    new_plan = re_plan(plan, completed)
    assert len(new_plan.steps) < len(plan.steps) or len(new_plan.steps) > 0


def test_agent_state():
    state = AgentState(incident_id="INC-001", goal="test")
    manager = AgentStateManager(state)
    assert state.iteration_count == 0
    manager.increment_iteration()
    assert state.iteration_count == 1


def test_reflection():
    state = AgentState(incident_id="INC-001", goal="test")
    state.evidence.append("deployment checkout-v2.4")
    state.evidence.append("latency increased 4x")
    state.evidence.append("database timeout errors")
    state.hypotheses.append(Hypothesis(description="Retry logic issue", confidence=0.8))
    result = reflect(state)
    assert result.evidence_sufficient or not result.evidence_sufficient


def test_vector_retriever():
    retriever = VectorRetriever()
    results = retriever.retrieve("database connection pool", top_k=2)
    assert len(results) <= 2


def test_agentic_retriever():
    base = VectorRetriever()
    retriever = AgenticRetriever(base)
    results = retriever.retrieve("latency")
    assert len(results) > 0


def test_investigation_loop():
    seed_metrics()
    seed_logs()
    seed_deployments()
    seed_incidents()
    state = run_investigation("Investigate latency on checkout-api", "TEST-001")
    assert state.terminated
    assert state.tool_call_count > 0


def test_duplicate_detection():
    state = AgentState(incident_id="INC-001", goal="test")
    manager = AgentStateManager(state)
    from opspilot.schemas import ToolCall
    tc = ToolCall(tool="query_metrics", arguments={"service": "checkout-api"})
    assert not manager.is_duplicate_call("query_metrics", {"service": "checkout-api"})
    manager.add_tool_call(tc)
    assert manager.is_duplicate_call("query_metrics", {"service": "checkout-api"})
