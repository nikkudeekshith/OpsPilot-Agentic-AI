from __future__ import annotations
import json
import re
from opspilot.schemas import (
    AgentState, ToolCall, ToolResult, Plan, Step, Hypothesis, ApprovalRequest, IncidentReport,
)
from opspilot.tools.registry import ToolRegistry
from opspilot.state import AgentStateManager
from opspilot.planner import create_plan, re_plan
from opspilot.reflection import reflect
from opspilot.controls import AutonomousControls
from opspilot.human_approval import create_approval_request
from opspilot.rag.retriever import VectorRetriever, AgenticRetriever
from opspilot.observability import get_logger
from opspilot.llm import llm_complete, _fallback_llm


def _detect_service(goal: str) -> str:
    g = goal.lower()
    if "payment" in g and "checkout" not in g:
        return "payment-service"
    if "checkout" in g:
        return "checkout-api"
    if "user" in g:
        return "user-service"
    if "gateway" in g:
        return "payment-gateway"
    return "checkout-api"


def _detect_metric(goal: str) -> str:
    g = goal.lower()
    if "latency" in g or "p99" in g or "slow" in g:
        return "p99_latency_ms"
    if "error" in g or "fail" in g or "500" in g:
        return "error_rate_pct"
    if "cpu" in g:
        return "cpu_utilization_pct"
    if "memory" in g or "mem" in g:
        return "memory_usage_mb"
    if "timeout" in g or "database" in g or "db" in g or "connection" in g:
        return "p99_latency_ms"
    return "p99_latency_ms"


def _detect_keywords(goal: str) -> str:
    g = goal.lower()
    if "timeout" in g:
        return "timeout"
    if "latency" in g or "slow" in g:
        return "latency"
    if "error" in g or "fail" in g:
        return "error"
    if "database" in g or "db" in g or "connection" in g:
        return "timeout database"
    if "deploy" in g or "rollback" in g or "version" in g:
        return "deployment"
    if "memory" in g:
        return "memory"
    if "cpu" in g:
        return "cpu"
    return "latency timeout"


def _build_tool_args(step_tool: str, goal: str, step_desc: str, state: AgentState) -> dict:
    service = _detect_service(goal)
    metric = _detect_metric(goal)
    keywords = _detect_keywords(goal)

    if step_tool == "query_metrics":
        return {"service": service, "metric_name": metric}
    elif step_tool == "search_logs":
        level = "ERROR" if ("error" in goal.lower() or "fail" in goal.lower() or "timeout" in goal.lower()) else None
        args = {"service": service, "keywords": keywords}
        if level:
            args["level"] = level
        return args
    elif step_tool == "get_deployments":
        return {"service": service}
    elif step_tool == "search_incidents":
        return {"service": service, "keywords": keywords}
    elif step_tool == "retrieve_runbook":
        return {"query": step_desc}
    elif step_tool == "create_incident_report":
        return {
            "incident_id": state.incident_id,
            "root_cause": f"{service} issue related to {metric}",
            "confidence": 0.7,
            "evidence": state.evidence[-3:] if state.evidence else ["Investigation completed"],
            "recommended_action": f"Investigate {service} deployment" if "deploy" in goal.lower() else f"Review {service} {metric}",
            "requires_approval": False,
        }
    elif step_tool == "request_rollback":
        return {
            "service": service,
            "version": "v2.4" if "checkout" in service else "v1.9",
            "reason": goal,
            "evidence_summary": "; ".join(state.evidence[-3:]),
        }
    return {}


def _llm_decide(prompt: str) -> dict:
    result = llm_complete(prompt)
    try:
        parsed = json.loads(result)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        fallback = _fallback_llm(prompt)
        try:
            return json.loads(fallback)
        except (json.JSONDecodeError, TypeError):
            return {"tool": "query_metrics", "arguments": {"service": "checkout-api", "metric_name": "p99_latency_ms"}}
    return {"tool": "query_metrics", "arguments": {"service": "checkout-api", "metric_name": "p99_latency_ms"}}


def _summarize_evidence(state: AgentState) -> str:
    lines = []
    for obs in state.observations[-5:]:
        if obs.observation:
            lines.append(f"[{obs.tool}] {json.dumps(obs.observation, default=str)[:200]}")
    return "\n".join(lines)


def run_investigation(goal: str, incident_id: str = "INC-001") -> AgentState:
    import time as _time
    registry = ToolRegistry()
    retriever = AgenticRetriever(VectorRetriever())

    state = AgentState(incident_id=incident_id, goal=goal)
    state.plan = create_plan(goal)
    manager = AgentStateManager(state)
    controls = AutonomousControls(state)
    logger = get_logger()
    start_ts = _time.time()

    logger.log_step(state, f"Investigation started: {goal}")

    while not state.terminated:
        manager.increment_iteration()
        stop, reason = controls.should_stop()
        if stop:
            state.terminated = True
            state.termination_reason = reason
            logger.log_step(state, f"Terminated: {reason}")
            break

        plan_step: Step | None = None
        for step in state.plan.steps:
            if step.status == "pending":
                plan_step = step
                break

        if plan_step is None:
            completed = [s.description for s in state.plan.steps if s.status == "completed"]
            state_reflection = reflect(state)
            state.reflection = state_reflection
            logger.log_step(state, "Reflection", reflection=state_reflection.model_dump())

            if state_reflection.should_replan:
                new_plan = re_plan(state.plan, completed, "Investigate remaining evidence gaps")
                manager.update_plan(new_plan)
                logger.log_step(state, f"Re-planning: {new_plan.goal}")
                continue
            else:
                if state.hypotheses:
                    best = max(state.hypotheses, key=lambda h: h.confidence)
                    report = IncidentReport(
                        root_cause=best.description,
                        confidence=best.confidence,
                        evidence=state.evidence[-5:],
                        contradictory_evidence=state_reflection.contradictions,
                        alternative_hypotheses=state_reflection.alternative_hypotheses,
                        recommended_action=(
                            f"Rollback deployment associated with {best.description}" if best.confidence >= 0.8
                            else "Perform additional validation checks before remediation" if best.confidence >= 0.6
                            else "Further investigation required"
                        ),
                        requires_approval=best.confidence >= 0.8,
                    )
                    state.report = report
                    if report.requires_approval:
                        create_approval_request(
                            action="rollback",
                            target=goal.split(" ")[0] if " " in goal else goal,
                            reason=report.recommended_action,
                            evidence_summary="; ".join(state.evidence[-3:]),
                        )
                    state.terminated = True
                    state.termination_reason = "Investigation complete"
                    logger.log_step(state, "Investigation complete", reflection=state_reflection.model_dump())
                else:
                    state.terminated = True
                    state.termination_reason = "No hypothesis formed"
                break

        tool_spec = registry.get_spec(plan_step.tool)
        if tool_spec is None:
            plan_step.status = "failed"
            continue

        tool_call = ToolCall(tool=plan_step.tool, arguments=_build_tool_args(plan_step.tool, goal, plan_step.description, state))

        if manager.is_duplicate_call(tool_call.tool, tool_call.arguments):
            if controls.check_repeated_call(tool_call):
                state.retry_count += 1
                if state.retry_count >= state.max_retries:
                    state.terminated = True
                    state.termination_reason = "Max retries reached due to duplicate calls"
                    break
                alt_args = dict(tool_call.arguments)
                if "limit" in alt_args:
                    alt_args["limit"] = alt_args.get("limit", 10) + 10
                else:
                    alt_args["limit"] = 20
                tool_call.arguments = alt_args

        available_params = list(tool_spec.parameters.keys())
        param_error = controls.check_invalid_arguments(tool_call, available_params)
        if param_error:
            tool_call.arguments = {}

        manager.add_tool_call(tool_call)
        result = registry.execute(tool_call.tool, tool_call.arguments)

        if not result.success:
            state.retry_count += 1
            plan_step.status = "failed"
            logger.log_step(state, f"Tool failed: {result.error}", tool_call=tool_call.model_dump(), result=result.model_dump())
            continue

        if controls.check_empty_observation(result):
            alt_args = dict(tool_call.arguments)
            alt_args["limit"] = alt_args.get("limit", 10) + 10
            result = registry.execute(tool_call.tool, alt_args)

        manager.add_observation(result)
        plan_step.status = "completed"

        rag_context = retriever.retrieve(plan_step.description)
        if rag_context:
            state.evidence.append(f"[RAG] {rag_context[0]['title']}: {rag_context[0]['content'][:200]}")

        observation_text = str(result.observation)[:300]
        hypothesis_prompt = (
            f"Based on the observation from {tool_call.tool}: {observation_text}\n"
            f"Current evidence: {'; '.join(state.evidence[-3:])}\n"
            f"Form a hypothesis about the root cause. Return JSON with 'hypothesis' and 'confidence' (0-1)."
        )
        hypo_result = _llm_decide(hypothesis_prompt)
        new_desc = hypo_result.get("hypothesis", f"Evidence from {tool_call.tool} suggests a potential issue")
        is_duplicate = any(h.description == new_desc for h in state.hypotheses)
        if not is_duplicate:
            hypothesis = Hypothesis(
                description=new_desc,
                confidence=hypo_result.get("confidence", 0.5),
                supporting_evidence=[observation_text],
            )
            manager.add_hypothesis(hypothesis)

        logger.log_step(state, f"Executed {tool_call.tool}", tool_call=tool_call.model_dump(), result=result.model_dump())

    state.execution_time = round(_time.time() - start_ts, 2)
    return state
