from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from pipeline.canonicalizer import dedupe_payload
from pipeline.document_reader import read_document
from pipeline.edge_endpoints import ensure_edge_endpoints, load_existing_nodes_from_jsonl
from pipeline.extractor import build_extractor
from pipeline.id_generator import ingestion_branch
from pipeline.ingest import add_run_metadata
from pipeline.jsonl_writer import write_jsonl
from pipeline.models import ExtractionPayload

from ..config import ApiSettings
from ..database import connect, row_to_dict, rows_to_dicts
from ..models import STATUS_FAILED, STATUS_PENDING_REVIEW
from .audit_service import AuditService
from .omnigraph_service import OmnigraphError, OmnigraphService


ACTOR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@:-]{1,79}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_actor(actor: str) -> str:
    if not ACTOR_RE.match(actor):
        raise HTTPException(status_code=400, detail="Invalid actor identifier")
    return actor


class IngestionService:
    def __init__(self, settings: ApiSettings, omnigraph: OmnigraphService, audit: AuditService):
        self.settings = settings
        self.omnigraph = omnigraph
        self.audit = audit

    def validate_source_path(self, source_path: str) -> Path:
        if "\x00" in source_path:
            raise HTTPException(status_code=400, detail="Invalid source path")
        candidate = (self.settings.repo_root / source_path).resolve()
        allowed_roots = [
            (self.settings.repo_root / "seed-data").resolve(),
            self.settings.allowed_upload_dir,
        ]
        if not any(candidate == root or root in candidate.parents for root in allowed_roots):
            raise HTTPException(status_code=400, detail="Source path is not in an allowed directory")
        if not candidate.is_file():
            raise HTTPException(status_code=404, detail="Source document not found")
        return candidate

    def create_ingestion(self, source_path: str, actor: str, extraction_provider: str) -> dict[str, Any]:
        validate_actor(actor)
        if extraction_provider not in {"rule-based", "mock", "llm"}:
            raise HTTPException(status_code=400, detail="Unsupported extraction provider")
        document_path = self.validate_source_path(source_path)
        document = read_document(document_path)
        branch_name = ingestion_branch(document.path, document.content_hash)
        run_id = f"run-{uuid.uuid4().hex[:16]}"
        relative_source = str(document_path.relative_to(self.settings.repo_root)).replace("\\", "/")
        created_at = utc_now()

        try:
            extractor = build_extractor(extraction_provider)
            existing_nodes = self._existing_product_feature_nodes()
            payload = add_run_metadata(
                extractor.extract(document),
                document,
                branch_name,
                extractor.model_name,
                self.settings.prompt_version,
            )
            payload = dedupe_payload(ensure_edge_endpoints(payload, existing_nodes=existing_nodes))
            payload = self._remove_duplicate_main_edges(payload)
            output_path = self.settings.ingest_output_dir / f"{branch_name}.jsonl"
            write_jsonl(payload, output_path)
            self.omnigraph.create_branch(branch_name, from_branch="main")
            self.omnigraph.load_jsonl(branch_name, output_path, actor=actor)
            summary = payload.review_summary()
            self._insert_run(
                run_id=run_id,
                source_path=relative_source,
                source_hash=document.content_hash,
                branch_name=branch_name,
                extraction_provider=extraction_provider,
                extraction_model=extractor.model_name,
                ingestion_actor=actor,
                status=STATUS_PENDING_REVIEW,
                created_at=created_at,
                summary=summary,
                jsonl_path=str(output_path),
                error_message=None,
            )
            self.audit.record(run_id, actor, "ingestion_created", {"branch_name": branch_name, "source_path": relative_source})
            run = self.get_run(run_id)
            run["review_url"] = f"/reviews/{run_id}"
            return run
        except Exception as exc:
            self._insert_run(
                run_id=run_id,
                source_path=relative_source,
                source_hash=document.content_hash,
                branch_name=branch_name,
                extraction_provider=extraction_provider,
                extraction_model="unknown",
                ingestion_actor=actor,
                status=STATUS_FAILED,
                created_at=created_at,
                summary={},
                jsonl_path="",
                error_message=str(exc),
            )
            self.audit.record(run_id, actor, "ingestion_failed", {"branch_name": branch_name, "error": str(exc)})
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(status_code=500, detail="Ingestion failed") from exc

    def list_runs(self, status: str | None = None) -> list[dict[str, Any]]:
        with connect(self.settings.database_path) as connection:
            if status:
                rows = connection.execute(
                    "select * from ingestion_runs where status = ? order by created_at desc",
                    (status,),
                ).fetchall()
            else:
                rows = connection.execute("select * from ingestion_runs order by created_at desc").fetchall()
        return rows_to_dicts(rows)

    def get_run(self, run_id: str) -> dict[str, Any]:
        with connect(self.settings.database_path) as connection:
            row = connection.execute("select * from ingestion_runs where run_id = ?", (run_id,)).fetchone()
        run = row_to_dict(row)
        if run is None:
            raise HTTPException(status_code=404, detail="Ingestion run not found")
        return run

    def update_run(self, run_id: str, **updates: Any) -> dict[str, Any]:
        if not updates:
            return self.get_run(run_id)
        assignments = []
        values = []
        for key, value in updates.items():
            assignments.append(f"{key} = ?")
            if key == "merge_result" and value is not None:
                values.append(json.dumps(value, sort_keys=True))
            else:
                values.append(value)
        values.append(run_id)
        with connect(self.settings.database_path) as connection:
            connection.execute(f"update ingestion_runs set {', '.join(assignments)} where run_id = ?", values)
        return self.get_run(run_id)

    def _existing_product_feature_nodes(self) -> dict[str, Any]:
        lines: list[str] = []
        for node_type in ("Product", "Feature"):
            for record in self.omnigraph.export_branch("main", type_name=node_type):
                lines.append(json.dumps(record, sort_keys=True))
        return load_existing_nodes_from_jsonl(lines)

    def _remove_duplicate_main_edges(self, payload: ExtractionPayload) -> ExtractionPayload:
        main_edges: dict[tuple[str, str, str], dict[str, Any]] = {}
        for record in self.omnigraph.export_branch("main"):
            if "edge" in record:
                main_edges[(record["edge"], record["from"], record["to"])] = self._meaningful_edge_data(record.get("data") or {})
        filtered_edges = []
        conflicts = []
        for edge in payload.edges:
            key = (edge.edge, edge.from_slug, edge.to_slug)
            current = main_edges.get(key)
            new_data = self._meaningful_edge_data(edge.to_omnigraph()["data"])
            if current is None:
                filtered_edges.append(edge)
            elif current != new_data:
                conflicts.append({"edge": edge.edge, "from": edge.from_slug, "to": edge.to_slug})
        if conflicts:
            raise RuntimeError(f"Equivalent edge keys already exist in main with different properties: {conflicts}")
        return ExtractionPayload(nodes=payload.nodes, edges=filtered_edges)

    def _meaningful_edge_data(self, data: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in sorted(data.items()) if key not in {"id", "created_at", "edge"}}

    def _insert_run(
        self,
        run_id: str,
        source_path: str,
        source_hash: str,
        branch_name: str,
        extraction_provider: str,
        extraction_model: str,
        ingestion_actor: str,
        status: str,
        created_at: str,
        summary: dict[str, Any],
        jsonl_path: str,
        error_message: str | None,
    ) -> None:
        with connect(self.settings.database_path) as connection:
            connection.execute(
                """
                insert into ingestion_runs (
                    run_id, source_path, source_document_hash, branch_name,
                    extraction_provider, extraction_model, ingestion_actor, status, created_at,
                    summary_json, jsonl_path, error_message
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    source_path,
                    source_hash,
                    branch_name,
                    extraction_provider,
                    extraction_model,
                    ingestion_actor,
                    status,
                    created_at,
                    json.dumps(summary, sort_keys=True),
                    jsonl_path,
                    error_message,
                ),
            )
