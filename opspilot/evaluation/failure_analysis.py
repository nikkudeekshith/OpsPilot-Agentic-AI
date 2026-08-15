from __future__ import annotations
from opspilot.evaluation.pipeline import run_evaluation


def generate_failure_analysis() -> str:
    results = run_evaluation()
    lines = []
    lines.append("=" * 70)
    lines.append("  OPsPILOT EVALUATION & FAILURE ANALYSIS REPORT")
    lines.append("=" * 70)
    lines.append("")

    lines.append("1. EXECUTIVE SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Total Scenarios Evaluated:  {results['total_scenarios']}")
    lines.append(f"  Investigation Success Rate: {results['investigation_success_rate']:.1%}")
    lines.append(f"  Tool Selection Accuracy:    {results['tool_selection_accuracy']:.1%}")
    lines.append(f"  Root Cause Accuracy:        {results['root_cause_accuracy']:.1%}")
    lines.append(f"  Average Tool Calls:         {results['average_tool_calls']}")
    lines.append(f"  Average Confidence:         {results['average_confidence']:.1%}")
    lines.append(f"  Evidence Grounded Rate:     {results['evidence_grounded_rate']:.1%}")
    lines.append(f"  Loop Completion Rate:       {results['loop_completion_rate']:.1%}")
    lines.append("")

    lines.append("2. SCENARIO RESULTS OVERVIEW")
    lines.append("-" * 40)
    low_rc = [s for s in results["scenario_results"] if s["root_cause_accuracy"] < 0.5]
    mid_rc = [s for s in results["scenario_results"] if 0.5 <= s["root_cause_accuracy"] < 0.8]
    high_rc = [s for s in results["scenario_results"] if s["root_cause_accuracy"] >= 0.8]
    lines.append(f"  High root cause accuracy (>=80%):   {len(high_rc)} scenarios")
    lines.append(f"  Medium root cause accuracy (50-79%): {len(mid_rc)} scenarios")
    lines.append(f"  Low root cause accuracy (<50%):      {len(low_rc)} scenarios")
    lines.append("")

    lines.append("3. FAILURE ANALYSIS — LOW-PERFORMING SCENARIOS")
    lines.append("-" * 40)
    if low_rc:
        for s in low_rc:
            lines.append(f"\n  Scenario {s['id']}: {s['goal'][:80]}")
            lines.append(f"  └ Root Cause Accuracy: {s['root_cause_accuracy']:.1%}")
            lines.append(f"  └ Tool Selection:     {s['tool_selection_accuracy']:.1%}")
            lines.append(f"  └ Tools Used:         {s['tools_used']}")

            reasons = []
            if s["root_cause_accuracy"] < 0.3:
                reasons.append("Hypothesis generation failed to match expected root cause pattern")
            if s["tool_selection_accuracy"] < 0.5:
                reasons.append("Incorrect or incomplete tool selection during investigation")
            if not s["tools_used"]:
                reasons.append("No tools executed — agent terminated before investigation")
            if s["confidence"] < 0.5:
                reasons.append("Low confidence suggests insufficient evidence gathering")
            if not reasons:
                reasons.append("Root cause identified but wording differs from expected pattern")

            for r in reasons:
                lines.append(f"  └ Reason: {r}")
    else:
        lines.append("  No low-performing scenarios detected.")
    lines.append("")

    lines.append("4. LIMITATIONS IDENTIFIED")
    lines.append("-" * 40)
    limitations = [
        ("LLM Dependency", "Without a real LLM API key (OpenAI/Gemini), the agent relies on a "
         "rule-based fallback that generates generic hypotheses. This limits root cause accuracy "
         "and prevents nuanced reasoning."),
        ("Synthetic Data", "All metrics, logs, deployments, and incidents are synthetic. The agent "
         "cannot generalize to real-world infrastructure without connecting to actual monitoring systems."),
        ("No Persistent Storage", "Agent state, trajectories, and approval requests live only in "
         "memory. Restarting the application loses all investigation history."),
        ("Static Knowledge Base", "The RAG layer uses a fixed set of 8 documents. There is no "
         "mechanism for adding new runbooks or updating existing documentation."),
        ("Limited Tool Scope", "Only 7 tools are implemented. Real incident investigation may "
         "require additional tools like tracing, configuration management, or feature flags."),
        ("No Parallel Execution", "Each scenario runs sequentially in the evaluation pipeline. "
         "For 30 scenarios, this takes significant time."),
        ("No Multi-turn Conversation", "The agent runs a single investigation and terminates. "
         "There is no follow-up Q&A or interactive refinement with the user."),
    ]
    for i, (title, desc) in enumerate(limitations, 1):
        lines.append(f"  {i}. {title}")
        lines.append(f"     {desc}")
    lines.append("")

    lines.append("5. PROPOSED IMPROVEMENTS")
    lines.append("-" * 40)
    improvements = [
        ("Real LLM Integration", "Connect to OpenAI, Gemini, or a local LLM (via Ollama) for "
         "genuine reasoning, hypothesis generation, and tool selection."),
        ("Live Monitoring Integration", "Replace synthetic data with real Prometheus/Datadog APIs, "
         "log aggregation services, and deployment platforms."),
        ("Persistent Database", "Use SQLite or PostgreSQL to persist agent state, trajectories, "
         "and approval requests across sessions."),
        ("Dynamic Knowledge Ingestion", "Allow users to upload runbooks, architecture docs, and "
         "incident post-mortems via the UI. Auto-chunk and embed them."),
        ("Expanded Tool Suite", "Add tools for distributed tracing, configuration diffs, feature "
         "flag analysis, load testing, and canary analysis."),
        ("Parallel Scenario Execution", "Use Python multiprocessing or async I/O to evaluate "
         "multiple scenarios concurrently, reducing evaluation time."),
        ("Conversational Interface", "Add follow-up questions capability so users can drill down "
         "into specific aspects of the investigation after the report is generated."),
        ("Confidence Calibration", "Implement a calibration step that adjusts confidence scores "
         "based on historical accuracy of similar hypotheses."),
        ("Security Hardening", "Add prompt injection detection for RAG-retrieved content, "
         "rate limiting on tool execution, and audit logging for all agent actions."),
    ]
    for i, (title, desc) in enumerate(improvements, 1):
        lines.append(f"  {i}. {title}")
        lines.append(f"     {desc}")
    lines.append("")

    lines.append("6. LESSONS LEARNED")
    lines.append("-" * 40)
    lessons = [
        "Agent loops need explicit termination conditions. Without max iteration limits, "
        "the agent can enter infinite re-plan cycles when evidence is insufficient.",
        "Tool argument validation is critical. Malformed arguments cause silent failures "
        "that are hard to debug without detailed trajectory logging.",
        "Duplicate call detection must consider semantic similarity, not just exact match. "
        "Two calls to query_metrics with different timestamps serve different purposes.",
        "Reflection must come after ALL plan steps are attempted, not just after the first "
        "pass. Premature reflection leads to unnecessary re-planning.",
        "The fallback LLM with keyword-based generation is surprisingly effective for "
        "structured scenarios but fails for edge cases and ambiguous incidents.",
        "Subprocess isolation for evaluation is essential to prevent state leakage between "
        "scenarios. Python module-level state (tool databases, trajectory logger) persists "
        "across calls unless explicitly reset or isolated.",
        "A dynamic tool registry is far more maintainable than if/elif chains. Adding a new "
        "tool requires only registering it — no changes to the execution loop.",
        "Human-in-the-loop is a critical safety feature. Even with high confidence, "
        "rollback decisions should never be fully automated in production.",
    ]
    for i, lesson in enumerate(lessons, 1):
        lines.append(f"  {i}. {lesson}")
    lines.append("")

    lines.append("7. DETAILED SCENARIO BREAKDOWN")
    lines.append("-" * 40)
    for s in results["scenario_results"]:
        status = "PASS" if s["success"] else "FAIL"
        lines.append(f"  [{status}] {s['id']}: {s['goal'][:70]}")
        lines.append(f"        RC Acc: {s['root_cause_accuracy']:.0%}  "
                     f"Tool Acc: {s['tool_selection_accuracy']:.0%}  "
                     f"Conf: {s['confidence']:.0%}  "
                     f"Tools: {len(s['tools_used'])}")
    lines.append("")

    lines.append("=" * 70)
    lines.append("  END OF REPORT")
    lines.append("=" * 70)

    return "\n".join(lines)
