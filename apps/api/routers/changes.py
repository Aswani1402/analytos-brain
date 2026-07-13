from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_audit_service, get_ingestion_service, get_omnigraph_service
from ..services.audit_service import AuditService
from ..services.ingestion_service import IngestionService
from ..services.omnigraph_service import OmnigraphService

router = APIRouter(prefix="/changes", tags=["changes"])


@router.get("/recent")
def recent_changes(
    omnigraph: OmnigraphService = Depends(get_omnigraph_service),
    audit: AuditService = Depends(get_audit_service),
    ingestion: IngestionService = Depends(get_ingestion_service),
):
    runs = {run["branch_name"]: run["run_id"] for run in ingestion.list_runs()}
    commits = []
    for commit in omnigraph.list_commits(branch="main"):
        branch = commit.get("branch") if isinstance(commit, dict) else None
        commits.append(
            {
                "commit": commit,
                "actor": commit.get("actor") if isinstance(commit, dict) else None,
                "timestamp": commit.get("timestamp") if isinstance(commit, dict) else None,
                "branch": branch,
                "related_ingestion_run": runs.get(branch) if branch else None,
            }
        )
    return {"commits": commits, "workflow_actions": audit.recent()}
