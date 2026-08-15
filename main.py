from __future__ import annotations
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from opspilot.loop import run_investigation
from opspilot.evaluation.pipeline import run_evaluation
from opspilot.evaluation.failure_analysis import generate_failure_analysis
from opspilot.tools.metrics import seed_metrics
from opspilot.tools.logs import seed_logs
from opspilot.tools.deployments import seed_deployments
from opspilot.tools.incidents import seed_incidents


def cli():
    seed_metrics()
    seed_logs()
    seed_deployments()
    seed_incidents()

    if len(sys.argv) > 1 and sys.argv[1] == "evaluate":
        print("Running evaluation...")
        results = run_evaluation()
        print(f"\nResults: {results['total_scenarios']} scenarios")
        print(f"  Success Rate: {results['investigation_success_rate']:.1%}")
        print(f"  Tool Selection Accuracy: {results['tool_selection_accuracy']:.1%}")
        print(f"  Root Cause Accuracy: {results['root_cause_accuracy']:.1%}")
        print(f"  Avg Tool Calls: {results['average_tool_calls']}")
        print(f"  Evidence Grounded: {results['evidence_grounded_rate']:.1%}")
        return

    if len(sys.argv) > 1 and sys.argv[1] == "failure-analysis":
        print(generate_failure_analysis())
        return

    goal = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Investigate why checkout API latency increased in the last two hours"
    print(f"Goal: {goal}")
    print("Starting investigation...\n")

    state = run_investigation(goal)

    print("\n" + "=" * 50)
    print("INVESTIGATION COMPLETE")
    print("=" * 50)
    print(f"Terminated: {state.termination_reason}")
    print(f"Iterations: {state.iteration_count}")
    print(f"Tool Calls: {state.tool_call_count}")

    if state.report:
        print(f"\n--- INCIDENT REPORT ---")
        print(f"Root Cause: {state.report.root_cause}")
        print(f"Confidence: {state.report.confidence:.0%}")
        print(f"Recommended Action: {state.report.recommended_action}")
        if state.report.evidence:
            print("Evidence:")
            for e in state.report.evidence:
                print(f"  - {e[:150]}...")
        if state.report.requires_approval:
            print("\n[!] Human approval required for rollback action")

    if state.hypotheses:
        print(f"\nHypotheses ({len(state.hypotheses)}):")
        for h in state.hypotheses:
            print(f"  [{h.confidence:.0%}] {h.description[:120]}")


if __name__ == "__main__":
    cli()
