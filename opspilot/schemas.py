from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ToolCategory(str, Enum):
    READ = "read"
    WRITE = "write"
    APPROVAL = "approval"


class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    category: ToolCategory = ToolCategory.READ
    required_approval: bool = False


class ToolCall(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    id: str = ""


class ToolResult(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    observation: Any = None
    error: str | None = None
    success: bool = True


class Step(BaseModel):
    description: str
    tool: str | None = None
    goal: str = ""
    dependency: list[str] = Field(default_factory=list)
    status: str = "pending"


class Plan(BaseModel):
    goal: str
    steps: list[Step] = Field(default_factory=list)


class Hypothesis(BaseModel):
    description: str
    confidence: float = 0.0
    supporting_evidence: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)


class IncidentReport(BaseModel):
    root_cause: str
    confidence: float
    evidence: list[str] = Field(default_factory=list)
    contradictory_evidence: list[str] = Field(default_factory=list)
    alternative_hypotheses: list[str] = Field(default_factory=list)
    recommended_action: str
    requires_approval: bool = True


class ReflectionResult(BaseModel):
    evidence_sufficient: bool
    alternative_hypotheses: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    skipped_steps: list[str] = Field(default_factory=list)
    critique: str = ""
    reasoning: str = ""
    should_replan: bool = False


class ApprovalRequest(BaseModel):
    action: str
    target: str
    reason: str
    evidence_summary: str
    approved: bool | None = None


class AgentState(BaseModel):
    incident_id: str
    goal: str
    plan: Plan = Plan(goal="")
    observations: list[ToolResult] = Field(default_factory=list)
    tool_history: list[ToolCall] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 20
    tool_call_count: int = 0
    max_tool_calls: int = 50
    retry_count: int = 0
    max_retries: int = 3
    terminated: bool = False
    termination_reason: str = ""
    approval_pending: ApprovalRequest | None = None
    report: IncidentReport | None = None
    reflection: ReflectionResult | None = None
    execution_time: float = 0.0
    trajectory: list[dict[str, Any]] = Field(default_factory=list)
