from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IngestionCreate(BaseModel):
    source_path: str
    actor: str = Field(min_length=2, max_length=80)
    extraction_provider: str = "rule-based"


class ApprovalRequest(BaseModel):
    reviewer_actor: str = Field(min_length=2, max_length=80)


class RejectionRequest(BaseModel):
    reviewer_actor: str = Field(min_length=2, max_length=80)
    reason: str = Field(min_length=1, max_length=1000)


class ContentAgentRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    actor: str = Field(default="content-agent", min_length=2, max_length=80)
    generation_mode: str = "deterministic"


class GTMAgentRequest(BaseModel):
    product: str = Field(min_length=1, max_length=100)
    actor: str = Field(default="gtm-agent", min_length=2, max_length=80)
    generation_mode: str = "deterministic"


class WorkflowRun(BaseModel):
    run_id: str
    source_path: str
    source_document_hash: str
    branch_name: str
    extraction_provider: str
    extraction_model: str
    status: str
    created_at: str
    reviewer_actor: str | None = None
    reviewed_at: str | None = None
    rejection_reason: str | None = None
    merge_result: dict[str, Any] | None = None
    summary: dict[str, Any]
    jsonl_path: str
    error_message: str | None = None


class HealthResponse(BaseModel):
    api: dict[str, Any]
    sqlite: dict[str, Any]
    omnigraph: dict[str, Any]
