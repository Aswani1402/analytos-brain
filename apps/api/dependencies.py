from __future__ import annotations

from fastapi import Request

from .config import ApiSettings
from .services.audit_service import AuditService
from .services.diff_service import DiffService
from .services.ingestion_service import IngestionService
from .services.omnigraph_service import OmnigraphService
from .services.review_service import ReviewService


def get_settings(request: Request) -> ApiSettings:
    return request.app.state.settings


def get_omnigraph_service(request: Request) -> OmnigraphService:
    return request.app.state.omnigraph_service


def get_ingestion_service(request: Request) -> IngestionService:
    return request.app.state.ingestion_service


def get_diff_service(request: Request) -> DiffService:
    return request.app.state.diff_service


def get_review_service(request: Request) -> ReviewService:
    return request.app.state.review_service


def get_audit_service(request: Request) -> AuditService:
    return request.app.state.audit_service
