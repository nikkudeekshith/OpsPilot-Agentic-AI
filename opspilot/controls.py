from __future__ import annotations
from opspilot.schemas import AgentState, ToolCall, ToolResult


class AutonomousControls:
    def __init__(self, state: AgentState):
        self.state = state

    def check_repeated_call(self, tool_call: ToolCall) -> bool:
        recent = self.state.tool_history[-3:] if len(self.state.tool_history) >= 3 else self.state.tool_history
        count = sum(1 for c in recent if c.tool == tool_call.tool and c.arguments == tool_call.arguments)
        return count >= 2

    def check_invalid_arguments(self, tool_call: ToolCall, available_params: list[str]) -> str | None:
        for key in tool_call.arguments:
            if key not in available_params:
                return f"Unknown argument '{key}' for tool '{tool_call.tool}'"
        return None

    def check_tool_failure(self, result: ToolResult) -> bool:
        return not result.success

    def check_empty_observation(self, result: ToolResult) -> bool:
        if result.observation is None:
            return True
        if isinstance(result.observation, dict):
            if "data" in result.observation and not result.observation["data"]:
                return True
            if "logs" in result.observation and not result.observation["logs"]:
                return True
            if "results" in result.observation and not result.observation["results"]:
                return True
        return False

    def should_stop(self) -> tuple[bool, str]:
        if self.state.tool_call_count >= self.state.max_tool_calls:
            return True, "Tool call limit exceeded"
        if self.state.iteration_count >= self.state.max_iterations:
            return True, "Iteration limit exceeded"
        if self.state.retry_count >= self.state.max_retries:
            return True, "Retry limit exceeded"
        return False, ""
