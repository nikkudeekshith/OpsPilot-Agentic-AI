from __future__ import annotations
from opspilot.schemas import Plan, Step


INVESTIGATION_TEMPLATES = {
    "latency": Plan(
        goal="Investigate latency increase and identify root cause",
        steps=[
            Step(description="Query latency metrics for the affected service", tool="query_metrics", goal="Get latency baseline and anomaly window"),
            Step(description="Search for ERROR/WARN logs around the anomaly time", tool="search_logs", goal="Find error patterns"),
            Step(description="Check recent deployments for the service", tool="get_deployments", goal="Identify deployment changes"),
            Step(description="Search for similar historical incidents", tool="search_incidents", goal="Find past patterns"),
            Step(description="Query CPU and memory metrics", tool="query_metrics", goal="Check resource utilization"),
            Step(description="Retrieve runbook for latency investigation", tool="retrieve_runbook", goal="Follow established procedures"),
        ],
    ),
    "error_rate": Plan(
        goal="Investigate error rate increase and identify root cause",
        steps=[
            Step(description="Query error rate metrics", tool="query_metrics", goal="Quantify error rate change"),
            Step(description="Search ERROR logs", tool="search_logs", goal="Identify error types"),
            Step(description="Check recent deployments", tool="get_deployments", goal="Find deployment correlation"),
            Step(description="Search for related incidents", tool="search_incidents", goal="Find known patterns"),
        ],
    ),
    "timeout": Plan(
        goal="Investigate timeout errors and database issues",
        steps=[
            Step(description="Query latency metrics for database-related patterns", tool="query_metrics", goal="Understand latency profile"),
            Step(description="Search for timeout and database ERROR logs", tool="search_logs", goal="Find timeout patterns"),
            Step(description="Check recent deployments affecting database", tool="get_deployments", goal="Find deployment that introduced retry logic"),
            Step(description="Search historical incidents for database timeouts", tool="search_incidents", goal="Compare with past incidents"),
            Step(description="Query CPU and memory metrics", tool="query_metrics", goal="Check for resource exhaustion"),
            Step(description="Retrieve runbook for database timeout", tool="retrieve_runbook", goal="Follow runbook steps"),
        ],
    ),
}

DEFAULT_PLAN = Plan(
    goal="Investigate incident using systematic approach",
    steps=[
        Step(description="Query basic metrics for the service", tool="query_metrics", goal="Establish baseline"),
        Step(description="Search for error logs", tool="search_logs", goal="Find error patterns"),
        Step(description="Check deployments", tool="get_deployments", goal="Identify changes"),
        Step(description="Search for related incidents", tool="search_incidents", goal="Historical context"),
        Step(description="Retrieve relevant runbook", tool="retrieve_runbook", goal="Follow procedures"),
    ],
)


def create_plan(goal: str) -> Plan:
    goal_lower = goal.lower()
    if "latency" in goal_lower:
        return INVESTIGATION_TEMPLATES["latency"]
    if "error" in goal_lower or "fail" in goal_lower:
        return INVESTIGATION_TEMPLATES["error_rate"]
    if "timeout" in goal_lower or "database" in goal_lower or "db" in goal_lower:
        return INVESTIGATION_TEMPLATES["timeout"]
    return DEFAULT_PLAN


def re_plan(plan: Plan, completed_step_descriptions: list[str],
            new_goal: str | None = None) -> Plan:
    if new_goal:
        return create_plan(new_goal)
    remaining = [s for s in plan.steps if s.description not in completed_step_descriptions]
    if not remaining:
        remaining = [Step(description="Perform deeper investigation: check resource metrics and logs with different filters",
                          tool="query_metrics", goal="Gather additional evidence")]
    return Plan(goal=plan.goal, steps=remaining)
