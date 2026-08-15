from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from opspilot.loop import run_investigation
from opspilot.evaluation.pipeline import run_evaluation
from opspilot.evaluation.failure_analysis import generate_failure_analysis
from opspilot.observability import get_logger
from opspilot.human_approval import get_pending_approvals, approve_request, deny_request
from opspilot.tools.metrics import seed_metrics
from opspilot.tools.logs import seed_logs
from opspilot.tools.deployments import seed_deployments
from opspilot.tools.incidents import seed_incidents

app = FastAPI(title="OpsPilot API", version="1.0.0")


class InvestigationRequest(BaseModel):
    goal: str
    incident_id: str = "INC-001"


class ApprovalAction(BaseModel):
    key: str
    approved: bool


@app.on_event("startup")
def _startup():
    seed_metrics()
    seed_logs()
    seed_deployments()
    seed_incidents()


@app.post("/investigate")
def investigate(req: InvestigationRequest):
    state = run_investigation(req.goal, req.incident_id)
    return {
        "incident_id": state.incident_id,
        "goal": state.goal,
        "terminated": state.terminated,
        "termination_reason": state.termination_reason,
        "iterations": state.iteration_count,
        "tool_calls": state.tool_call_count,
        "hypotheses": [h.model_dump() for h in state.hypotheses],
        "evidence": state.evidence,
        "report": state.report.model_dump() if state.report else None,
        "reflection": state.reflection.model_dump() if state.reflection else None,
        "tool_history": [t.model_dump() for t in state.tool_history],
    }


@app.get("/trajectory/{incident_id}")
def get_trajectory(incident_id: str):
    logger = get_logger()
    traj = logger.get_trajectory(incident_id)
    if not traj:
        raise HTTPException(404, f"No trajectory found for {incident_id}")
    return {"incident_id": incident_id, "trajectory": traj}


@app.get("/approvals/pending")
def list_pending_approvals():
    return {"approvals": [r.model_dump() for r in get_pending_approvals()]}


@app.post("/approvals/respond")
def respond_approval(action: ApprovalAction):
    if action.approved:
        req = approve_request(action.key)
    else:
        req = deny_request(action.key)
    if not req:
        raise HTTPException(404, f"No approval request found for key '{action.key}'")
    return {"message": "Approval updated", "request": req.model_dump()}


@app.post("/evaluate")
def evaluate():
    results = run_evaluation()
    return results


@app.get("/evaluate/failure-analysis")
def failure_analysis():
    return {"analysis": generate_failure_analysis()}


@app.get("/health")
def health():
    return {"status": "healthy"}
