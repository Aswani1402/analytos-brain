from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from agents.common import InsufficientEvidenceError
from agents.content_agent import run_content_agent
from agents.gtm_agent import run_gtm_agent

from ..dependencies import get_omnigraph_service
from ..schemas import ContentAgentRequest, GTMAgentRequest
from ..services.omnigraph_service import OmnigraphService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/content")
def content_agent(request: ContentAgentRequest, omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    try:
        return run_content_agent(
            omnigraph,
            request.topic,
            actor=request.actor,
            use_llm=request.generation_mode == "llm",
        )
    except InsufficientEvidenceError as exc:
        raise HTTPException(status_code=409, detail={"code": "insufficient_evidence", "message": str(exc)}) from exc


@router.post("/gtm")
def gtm_agent(request: GTMAgentRequest, omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    try:
        return run_gtm_agent(
            omnigraph,
            request.product,
            actor=request.actor,
            use_llm=request.generation_mode == "llm",
        )
    except InsufficientEvidenceError as exc:
        raise HTTPException(status_code=409, detail={"code": "insufficient_evidence", "message": str(exc)}) from exc
