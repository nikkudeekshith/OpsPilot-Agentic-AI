from __future__ import annotations
import os
import sys
import json
import subprocess
from opspilot.evaluation.scenarios import get_all_scenarios


class EvaluationResult:
    def __init__(self, scenario_id: str, scenario_goal: str):
        self.scenario_id = scenario_id
        self.scenario_goal = scenario_goal
        self.tools_used: list[str] = []
        self.tool_selection_accuracy: float = 0.0
        self.investigation_success: bool = False
        self.root_cause_accuracy: float = 0.0
        self.avg_tool_calls: int = 0
        self.loop_completed: bool = False
        self.evidence_grounded: bool = False
        self.confidence: float = 0.0
        self.errors: list[str] = []


def _run_scenario_in_process(scenario: dict) -> tuple[str, dict]:
    sid = scenario["id"]
    goal = json.dumps(scenario["goal"])
    inc_id = json.dumps(f"EVAL-{sid}")

    script_lines = [
        "import sys, json",
        "sys.stdout.reconfigure(encoding='utf-8')",
        "from opspilot.tools.metrics import seed_metrics",
        "from opspilot.tools.logs import seed_logs",
        "from opspilot.tools.deployments import seed_deployments",
        "from opspilot.tools.incidents import seed_incidents",
        "from opspilot.human_approval import reset_approvals",
        "from opspilot.loop import run_investigation",
        "seed_metrics(); seed_logs(); seed_deployments(); seed_incidents(); reset_approvals()",
        f"state = run_investigation({goal}, {inc_id})",
        "data = {",
        '  "tools_used": [t.tool for t in state.tool_history],',
        '  "terminated": state.terminated,',
        '  "termination_reason": state.termination_reason,',
        '  "evidence_count": len(state.evidence),',
        '  "report_conf": state.report.confidence if state.report else 0,',
        '  "report_rc": state.report.root_cause if state.report else "",',
        '  "hypothesis_count": len(state.hypotheses),',
        "}",
        'print(json.dumps(data))',
    ]
    script = "\n".join(script_lines)

    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=120,
            env=os.environ.copy(),
        )
        if result.returncode != 0:
            return sid, {"error": result.stderr[:500]}

        lines = result.stdout.strip().split("\n")
        output = lines[-1] if lines else ""
        data = json.loads(output)
        return sid, data
    except subprocess.TimeoutExpired:
        return sid, {"error": "timeout"}
    except Exception as e:
        return sid, {"error": str(e)}


def evaluate_scenario(scenario: dict) -> EvaluationResult:
    result = EvaluationResult(scenario["id"], scenario["goal"])
    sid, data = _run_scenario_in_process(scenario)

    if "error" in data:
        result.errors.append(data["error"])
        return result

    result.tools_used = data.get("tools_used", [])
    used_tools_set = set(result.tools_used)
    expected_set = set(scenario["expected_tools"])
    if used_tools_set:
        result.tool_selection_accuracy = len(used_tools_set & expected_set) / len(expected_set)

    reason = data.get("termination_reason", "")
    result.loop_completed = data.get("terminated", False) and (
        "complete" in reason.lower() or "sufficient" in reason.lower()
    )
    result.investigation_success = result.loop_completed
    result.avg_tool_calls = len(result.tools_used)

    report_conf = data.get("report_conf", 0)
    report_rc = data.get("report_rc", "")
    if report_rc:
        result.confidence = report_conf
        expected_rc = scenario["expected_root_cause"].lower()
        report_rc_lower = report_rc.lower()
        if expected_rc in report_rc_lower or report_rc_lower in expected_rc:
            result.root_cause_accuracy = 1.0
        else:
            common = len(set(expected_rc.split()) & set(report_rc_lower.split()))
            total = max(len(expected_rc.split()), 1)
            result.root_cause_accuracy = common / total

    result.evidence_grounded = data.get("evidence_count", 0) >= 2
    return result


def run_evaluation() -> dict:
    scenarios = get_all_scenarios()
    results = []

    for scenario in scenarios:
        eval_result = evaluate_scenario(scenario)
        results.append(eval_result)

    total = len(results)
    successful = sum(1 for r in results if r.investigation_success)
    avg_tool_accuracy = sum(r.tool_selection_accuracy for r in results) / total if total else 0
    avg_root_cause = sum(r.root_cause_accuracy for r in results) / total if total else 0
    avg_tool_calls = sum(r.avg_tool_calls for r in results) / total if total else 0
    avg_confidence = sum(r.confidence for r in results) / total if total else 0
    grounded = sum(1 for r in results if r.evidence_grounded)

    return {
        "total_scenarios": total,
        "investigation_success_rate": successful / total if total else 0,
        "tool_selection_accuracy": round(avg_tool_accuracy, 4),
        "root_cause_accuracy": round(avg_root_cause, 4),
        "average_tool_calls": round(avg_tool_calls, 2),
        "average_confidence": round(avg_confidence, 4),
        "evidence_grounded_rate": grounded / total if total else 0,
        "loop_completion_rate": sum(1 for r in results if r.loop_completed) / total if total else 0,
        "scenario_results": [
            {
                "id": r.scenario_id,
                "goal": r.scenario_goal,
                "success": r.investigation_success,
                "root_cause_accuracy": r.root_cause_accuracy,
                "tool_selection_accuracy": r.tool_selection_accuracy,
                "tools_used": r.tools_used,
                "confidence": r.confidence,
                "errors": r.errors,
            }
            for r in results
        ],
    }
