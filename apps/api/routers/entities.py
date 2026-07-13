from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_api_token
from ..dependencies import get_omnigraph_service
from ..services.omnigraph_service import OmnigraphService

router = APIRouter(prefix="/entities", tags=["entities"])


TYPE_ROUTES = {
    "products": "Product",
    "features": "Feature",
    "proof-points": "ProofPoint",
    "icp-segments": "ICPSegment",
    "personas": "Persona",
    "people": "Person",
    "email-threads": "EmailThread",
    "decisions": "Decision",
}


def _records_for_type(omnigraph: OmnigraphService, type_name: str) -> list[dict]:
    return sorted(omnigraph.export_branch("main", type_name=type_name), key=lambda record: (record.get("data") or {}).get("slug", ""))


@router.get("/products")
def products(omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    return _records_for_type(omnigraph, "Product")


@router.get("/products/{slug:path}")
def product_detail(slug: str, omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    product = omnigraph.execute_query("get_product", {"product_slug": slug}, branch="main")
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "product": product[0],
        "features": omnigraph.execute_query("get_product_features", {"product_slug": slug}, branch="main"),
        "proof_points": omnigraph.execute_query("get_product_proof_points", {"product_slug": slug}, branch="main"),
        "icp_segments": omnigraph.execute_query("get_product_icp_segments", {"product_slug": slug}, branch="main"),
    }


@router.get("/features")
def features(omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    return _records_for_type(omnigraph, "Feature")


@router.get("/proof-points")
def proof_points(omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    return _records_for_type(omnigraph, "ProofPoint")


@router.get("/icp-segments")
def icp_segments(omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    return _records_for_type(omnigraph, "ICPSegment")


@router.get("/personas")
def personas(omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    return _records_for_type(omnigraph, "Persona")


@router.get("/people")
def people(_auth: None = Depends(require_api_token), omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    return _records_for_type(omnigraph, "Person")


@router.get("/email-threads")
def email_threads(_auth: None = Depends(require_api_token), omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    return _records_for_type(omnigraph, "EmailThread")


@router.get("/decisions")
def decisions(omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    return _records_for_type(omnigraph, "Decision")
