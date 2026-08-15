from __future__ import annotations

_reports: list[dict] = []


def create_incident_report(incident_id: str, root_cause: str, confidence: float,
                           evidence: list[str], recommended_action: str,
                           requires_approval: bool = True) -> dict:
    report = {
        "incident_id": incident_id,
        "root_cause": root_cause,
        "confidence": confidence,
        "evidence": evidence,
        "recommended_action": recommended_action,
        "requires_approval": requires_approval,
        "status": "approval_pending" if requires_approval else "final",
    }
    _reports.append(report)
    return report
