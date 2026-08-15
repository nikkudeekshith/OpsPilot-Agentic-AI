from __future__ import annotations
from opspilot.schemas import AgentState, ReflectionResult, Hypothesis


def reflect(state: AgentState) -> ReflectionResult:
    evidence = state.evidence
    hypotheses = state.hypotheses
    observations = state.observations
    tool_history = state.tool_history

    contradictions = []
    for h in hypotheses:
        for obs in observations:
            if obs.observation and isinstance(obs.observation, dict):
                obs_str = str(obs.observation)
                for cntr in h.contradictions:
                    if cntr and cntr in obs_str:
                        contradictions.append(
                            f"Hypothesis '{h.description[:60]}...' contradicted by "
                            f"{obs.tool}: {cntr}"
                        )

    alt_hypotheses = []
    if len(hypotheses) < 2:
        alt_hypotheses.append("Could this be a resource exhaustion issue rather than a code defect?")
        alt_hypotheses.append("Could this be caused by external dependency degradation rather than an internal change?")
    else:
        reviewed = set()
        for h in hypotheses:
            low_conf = h.confidence < 0.5
            if low_conf and h.description not in reviewed:
                alt_hypotheses.append(f"Consider low-confidence hypothesis: {h.description[:80]}...")
                reviewed.add(h.description)

    skipped = []
    if state.plan.steps:
        called_tools = {t.tool for t in tool_history}
        for step in state.plan.steps:
            if step.tool and step.tool not in called_tools:
                skipped.append(f"{step.tool}: {step.description}")

    evidence_str = " ".join(evidence).lower() if evidence else ""
    has_latency = "latency" in evidence_str or "p99" in evidence_str
    has_deployment = "deployment" in evidence_str or "version" in evidence_str
    has_timeout = "timeout" in evidence_str or "database" in evidence_str
    has_error = "error" in evidence_str
    has_logs = any(o.tool == "search_logs" for o in observations)
    has_metrics = any(o.tool == "query_metrics" for o in observations)

    evidence_count = len(evidence)
    hypothesis_count = len(hypotheses)
    has_high_conf_hypothesis = any(h.confidence >= 0.7 for h in hypotheses)

    reasoning_parts = []

    if has_deployment and has_latency and has_timeout:
        evidence_sufficient = True
        reasoning_parts.append("Evidence shows deployment correlated with latency and timeout patterns")
    elif evidence_count >= 3 and hypothesis_count >= 1 and has_high_conf_hypothesis:
        evidence_sufficient = True
        reasoning_parts.append(f"Sufficient evidence ({evidence_count} items) with high-confidence hypothesis")
    elif evidence_count >= 4:
        evidence_sufficient = True
        reasoning_parts.append(f"Multiple evidence sources ({evidence_count} items) support conclusion")
    else:
        evidence_sufficient = False
        reasoning_parts.append(f"Insufficient evidence (only {evidence_count} items)")

    if not evidence_sufficient and not has_error and not has_timeout:
        evidence_sufficient = False
        reasoning_parts.append("No error or timeout patterns detected in evidence")

    if has_metrics and not has_logs:
        reasoning_parts.append("Metrics were queried but logs were not reviewed")
    if has_logs and not has_metrics:
        reasoning_parts.append("Logs were reviewed but metrics were not queried")

    critique_parts = []
    if not evidence_sufficient:
        critique_parts.append("Evidence is insufficient to form a confident conclusion")
    if contradictions:
        critique_parts.append(f"Found {len(contradictions)} contradictions between evidence and hypotheses")
    if skipped:
        critique_parts.append(f"Skipped {len(skipped)} investigation steps that could provide additional evidence")
    if hypothesis_count == 0:
        critique_parts.append("No hypotheses have been formed yet")
    if hypothesis_count > 3:
        critique_parts.append(f"Large number of hypotheses ({hypothesis_count}) suggests uncertainty")
    if evidence_count > 0 and hypothesis_count == 1:
        critique_parts.append("Only one hypothesis considered; alternative explanations may exist")

    should_replan = (not evidence_sufficient) or bool(contradictions) or (hypothesis_count == 0)

    if should_replan:
        reasoning_parts.append("Re-planning required to gather additional evidence")
    else:
        reasoning_parts.append("Evidence sufficient for conclusion")

    critique = "; ".join(critique_parts) if critique_parts else (
        "Investigation appears thorough and evidence is sufficient. "
        "No contradictions detected. All planned steps completed."
    )

    reasoning = "; ".join(reasoning_parts)

    return ReflectionResult(
        evidence_sufficient=evidence_sufficient,
        alternative_hypotheses=alt_hypotheses,
        contradictions=contradictions,
        skipped_steps=skipped,
        critique=critique,
        reasoning=reasoning,
        should_replan=should_replan,
    )
