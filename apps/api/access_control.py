from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException


ROLE_REVIEWER = "reviewer"
ROLE_CONTENT_AGENT = "content-agent"
ROLE_GTM_AGENT = "gtm-agent"
ROLE_DASHBOARD_READER = "dashboard-reader"
ROLE_INGESTION_SERVICE = "ingestion-service"


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def role_for_actor(actor: str | None) -> str:
    actor = (actor or "").strip()
    if actor.startswith("reviewer"):
        return ROLE_REVIEWER
    if actor.startswith("content-agent"):
        return ROLE_CONTENT_AGENT
    if actor.startswith("gtm-agent"):
        return ROLE_GTM_AGENT
    if actor.startswith("ingestion"):
        return ROLE_INGESTION_SERVICE
    if actor.startswith("dashboard"):
        return ROLE_DASHBOARD_READER
    return ROLE_DASHBOARD_READER


def decide(actor: str | None, action: str, *, branch: str = "main", node_type: str | None = None, approved_external: bool = False) -> PolicyDecision:
    role = role_for_actor(actor)
    if branch != "main" and role not in {ROLE_REVIEWER, ROLE_INGESTION_SERVICE}:
        return PolicyDecision(False, f"{role} cannot access pending branches")

    if action in {"approve", "reject", "merge", "delete_branch", "read_review_diff"}:
        return PolicyDecision(role == ROLE_REVIEWER, f"{role} is not allowed to {action}")
    if action in {"create_ingestion_branch", "write_ingestion_branch"}:
        return PolicyDecision(role == ROLE_INGESTION_SERVICE, f"{role} cannot write ingestion branches")
    if action in {"write_main", "direct_main_write"}:
        return PolicyDecision(False, "direct writes to main are denied")
    if action == "run_content_agent":
        return PolicyDecision(role == ROLE_CONTENT_AGENT, f"{role} cannot run Content Agent")
    if action == "run_gtm_agent":
        return PolicyDecision(role == ROLE_GTM_AGENT, f"{role} cannot run GTM Agent")

    if action == "read_node":
        if role == ROLE_CONTENT_AGENT:
            if node_type in {"Product", "Feature"}:
                return PolicyDecision(True, "content-agent may read safe product context")
            if node_type == "ProofPoint" and approved_external:
                return PolicyDecision(True, "content-agent may read externally approved proof points")
            return PolicyDecision(False, f"content-agent cannot read {node_type}")
        if role == ROLE_GTM_AGENT:
            if node_type in {"Product", "Feature", "ICPSegment", "Persona"}:
                return PolicyDecision(True, "gtm-agent may read GTM context")
            if node_type == "ProofPoint" and approved_external:
                return PolicyDecision(True, "gtm-agent may read externally approved proof points")
            return PolicyDecision(False, f"gtm-agent cannot read {node_type}")
        if role in {ROLE_REVIEWER, ROLE_DASHBOARD_READER, ROLE_INGESTION_SERVICE}:
            return PolicyDecision(True, f"{role} may read approved main")

    if action == "read_main":
        return PolicyDecision(role in {ROLE_REVIEWER, ROLE_CONTENT_AGENT, ROLE_GTM_AGENT, ROLE_DASHBOARD_READER}, f"{role} cannot read main")

    return PolicyDecision(False, f"No policy rule allows {role} to {action}")


def require_allowed(actor: str | None, action: str, **kwargs) -> None:
    decision = decide(actor, action, **kwargs)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)


def is_allowed_node(actor: str, record: dict, branch: str = "main") -> bool:
    data = record.get("data") or {}
    approved_external = data.get("approved_for_external_use") == "true" and data.get("visibility") == "external_approved"
    return decide(actor, "read_node", branch=branch, node_type=record.get("type"), approved_external=approved_external).allowed
