from __future__ import annotations

_rollback_requests: list[dict] = []


def request_rollback(service: str, version: str, reason: str,
                     evidence_summary: str, requested_by: str = "OpsPilot") -> dict:
    request = {
        "service": service,
        "version": version,
        "reason": reason,
        "evidence_summary": evidence_summary,
        "requested_by": requested_by,
        "status": "pending_approval",
    }
    _rollback_requests.append(request)
    return {
        "request": request,
        "message": f"Rollback request for {service} {version} created. Requires human approval.",
        "requires_approval": True,
    }
