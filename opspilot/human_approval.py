from __future__ import annotations
from opspilot.schemas import ApprovalRequest


_pending_approvals: dict[str, ApprovalRequest] = {}


def create_approval_request(action: str, target: str, reason: str, evidence_summary: str) -> ApprovalRequest:
    req = ApprovalRequest(
        action=action,
        target=target,
        reason=reason,
        evidence_summary=evidence_summary,
    )
    key = f"{action}:{target}"
    _pending_approvals[key] = req
    return req


def get_pending_approvals() -> list[ApprovalRequest]:
    return [r for r in _pending_approvals.values() if r.approved is None]


def approve_request(key: str) -> ApprovalRequest | None:
    req = _pending_approvals.get(key)
    if req:
        req.approved = True
    return req


def deny_request(key: str) -> ApprovalRequest | None:
    req = _pending_approvals.get(key)
    if req:
        req.approved = False
    return req


def reset_approvals():
    _pending_approvals.clear()
