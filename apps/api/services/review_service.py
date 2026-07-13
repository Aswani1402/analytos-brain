from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from ..models import STATUS_APPROVED, STATUS_PENDING_REVIEW, STATUS_REJECTED
from .audit_service import AuditService
from .diff_service import DiffService
from .ingestion_service import IngestionService, validate_actor
from .omnigraph_service import OmnigraphError, OmnigraphService


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReviewService:
    def __init__(
        self,
        ingestion: IngestionService,
        omnigraph: OmnigraphService,
        diff_service: DiffService,
        audit: AuditService,
    ):
        self.ingestion = ingestion
        self.omnigraph = omnigraph
        self.diff_service = diff_service
        self.audit = audit

    def pending_reviews(self) -> list[dict[str, Any]]:
        return self.ingestion.list_runs(status=STATUS_PENDING_REVIEW)

    def get_review(self, run_id: str) -> dict[str, Any]:
        run = self.ingestion.get_run(run_id)
        source_path = self.ingestion.settings.repo_root / run["source_path"]
        source_document = {
            "path": run["source_path"],
            "content": source_path.read_text(encoding="utf-8") if source_path.exists() else None,
            "hash": run["source_document_hash"],
        }
        diff = self.diff_service.diff(run["branch_name"]) if self.omnigraph.branch_exists(run["branch_name"]) else {}
        return {
            "run": run,
            "source_document": source_document,
            "branch_name": run["branch_name"],
            **diff,
        }

    def approve(self, run_id: str, reviewer_actor: str) -> dict[str, Any]:
        validate_actor(reviewer_actor)
        run = self.ingestion.get_run(run_id)
        if reviewer_actor == run.get("ingestion_actor"):
            raise HTTPException(status_code=403, detail="The ingestion actor cannot approve its own branch")
        if run["status"] != STATUS_PENDING_REVIEW:
            raise HTTPException(status_code=409, detail="Only pending_review runs can be approved")
        if not self.omnigraph.branch_exists(run["branch_name"]):
            raise HTTPException(status_code=409, detail="Ingestion branch no longer exists")

        diff = self.diff_service.diff(run["branch_name"])
        self._validate_safe_diff(diff)
        main_edge_keys = self.diff_service.business_edge_keys(self.omnigraph.export_branch("main"))
        added_edge_keys = self.diff_service.business_edge_keys(diff["added_edges"])
        duplicate_keys = sorted(main_edge_keys & added_edge_keys)
        if duplicate_keys:
            raise HTTPException(status_code=409, detail={"message": "Duplicate equivalent business edges found", "edges": duplicate_keys})

        merge_result = self.omnigraph.merge_branch(run["branch_name"], actor=reviewer_actor, target_branch="main")
        updated = self.ingestion.update_run(
            run_id,
            status=STATUS_APPROVED,
            reviewer_actor=reviewer_actor,
            reviewed_at=utc_now(),
            merge_result=merge_result,
        )
        self.audit.record(run_id, reviewer_actor, "review_approved", {"branch_name": run["branch_name"], "merge_result": merge_result})
        return {"run": updated, "diff": diff, "merge_result": merge_result}

    def reject(self, run_id: str, reviewer_actor: str, reason: str) -> dict[str, Any]:
        validate_actor(reviewer_actor)
        run = self.ingestion.get_run(run_id)
        if run["status"] != STATUS_PENDING_REVIEW:
            raise HTTPException(status_code=409, detail="Only pending_review runs can be rejected")
        if self.omnigraph.branch_exists(run["branch_name"]):
            self.omnigraph.delete_branch(run["branch_name"], actor=reviewer_actor)
        updated = self.ingestion.update_run(
            run_id,
            status=STATUS_REJECTED,
            reviewer_actor=reviewer_actor,
            reviewed_at=utc_now(),
            rejection_reason=reason,
        )
        self.audit.record(run_id, reviewer_actor, "review_rejected", {"branch_name": run["branch_name"], "reason": reason})
        return updated

    def _validate_safe_diff(self, diff: dict[str, Any]) -> None:
        unsafe: list[str] = []
        for record in diff.get("added_nodes", []):
            data = record.get("data") or {}
            if record.get("type") == "EmailThread" and data.get("visibility") != "internal":
                unsafe.append(f"EmailThread {data.get('slug')} is not internal")
            if record.get("type") == "ProofPoint":
                approved = data.get("approved_for_external_use")
                visibility = data.get("visibility")
                if approved == "true" and visibility not in {"external_approved", "internal"}:
                    unsafe.append(f"ProofPoint {data.get('slug')} has unsafe visibility")
        if diff.get("changed_edges"):
            unsafe.append("Changed edge properties require manual conflict handling")
        if unsafe:
            raise HTTPException(status_code=409, detail={"message": "Unsafe records found", "issues": unsafe})
