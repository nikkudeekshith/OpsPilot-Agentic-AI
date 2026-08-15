from __future__ import annotations
import json
import time
from opspilot.schemas import AgentState


class TrajectoryLogger:
    def __init__(self):
        self.trajectories: dict[str, list[dict]] = {}

    def log_step(self, state: AgentState, decision: str, tool_call: dict | None = None,
                 result: dict | None = None, reflection: dict | None = None):
        entry = {
            "timestamp": time.time(),
            "iteration": state.iteration_count,
            "tool_call_count": state.tool_call_count,
            "decision": decision,
            "tool_call": tool_call,
            "result": result,
            "reflection": reflection,
            "state_snapshot": {
                "hypotheses": [h.model_dump() for h in state.hypotheses],
                "evidence_count": len(state.evidence),
                "plan_step_count": len(state.plan.steps),
                "terminated": state.terminated,
            },
        }
        self.trajectories.setdefault(state.incident_id, []).append(entry)

    def get_trajectory(self, incident_id: str) -> list[dict]:
        return self.trajectories.get(incident_id, [])

    def get_all_trajectories(self) -> dict[str, list[dict]]:
        return self.trajectories

    def export_json(self, filepath: str):
        with open(filepath, "w") as f:
            json.dump(self.trajectories, f, indent=2, default=str)


_logger = TrajectoryLogger()


def get_logger() -> TrajectoryLogger:
    return _logger
