from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_ingestion_service
from ..auth import require_api_token
from ..schemas import IngestionCreate
from ..services.ingestion_service import IngestionService

router = APIRouter(prefix="/ingestions", tags=["ingestions"])


@router.post("")
def create_ingestion(
    request: IngestionCreate,
    _auth: None = Depends(require_api_token),
    service: IngestionService = Depends(get_ingestion_service),
):
    return service.create_ingestion(request.source_path, request.actor, request.extraction_provider)


@router.get("")
def list_ingestions(status: str | None = Query(default=None), service: IngestionService = Depends(get_ingestion_service)):
    return service.list_runs(status=status)


@router.get("/{run_id}")
def get_ingestion(run_id: str, service: IngestionService = Depends(get_ingestion_service)):
    return service.get_run(run_id)
