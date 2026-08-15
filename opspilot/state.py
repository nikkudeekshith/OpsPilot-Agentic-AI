from __future__ import annotations
from opspilot.schemas import AgentState, ToolCall, ToolResult, Plan, Step, Hypothesis


class AgentStateManager:
    def __init__(self, state: AgentState):
        self.state = state

    def add_tool_call(self, tool_call: ToolCall):
        self.state.tool_history.append(tool_call)
        self.state.tool_call_count += 1

    def add_observation(self, result: ToolResult):
        self.state.observations.append(result)
        if result.observation:
            obs_str = str(result.observation)
            if obs_str not in self.state.evidence:
                self.state.evidence.append(obs_str)

    def increment_iteration(self):
        self.state.iteration_count += 1

    def add_hypothesis(self, hypothesis: Hypothesis):
        self.state.hypotheses.append(hypothesis)

    def update_plan(self, plan: Plan):
        self.state.plan = plan

    def is_duplicate_call(self, tool: str, arguments: dict) -> bool:
        recent = self.state.tool_history[-5:] if len(self.state.tool_history) >= 5 else self.state.tool_history
        for call in recent:
            if call.tool == tool and call.arguments == arguments:
                return True
        return False

    def should_terminate(self) -> tuple[bool, str]:
        if self.state.terminated:
            return True, self.state.termination_reason
        if self.state.iteration_count >= self.state.max_iterations:
            return True, f"Max iterations ({self.state.max_iterations}) reached"
        if self.state.tool_call_count >= self.state.max_tool_calls:
            return True, f"Max tool calls ({self.state.max_tool_calls}) reached"
        if self.state.retry_count >= self.state.max_retries:
            return True, f"Max retries ({self.state.max_retries}) exceeded"
        return False, ""
