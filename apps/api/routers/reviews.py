from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_review_service
from ..schemas import ApprovalRequest, RejectionRequest
from ..services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("")
def list_reviews(service: ReviewService = Depends(get_review_service)):
    return service.pending_reviews()


@router.get("/{run_id}")
def get_review(run_id: str, service: ReviewService = Depends(get_review_service)):
    return service.get_review(run_id)


@router.post("/{run_id}/approve")
def approve(run_id: str, request: ApprovalRequest, service: ReviewService = Depends(get_review_service)):
    return service.approve(run_id, request.reviewer_actor)


@router.post("/{run_id}/reject")
def reject(run_id: str, request: RejectionRequest, service: ReviewService = Depends(get_review_service)):
    return service.reject(run_id, request.reviewer_actor, request.reason)
