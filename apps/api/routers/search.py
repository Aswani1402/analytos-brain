from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_omnigraph_service
from ..services.omnigraph_service import OmnigraphService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(q: str = Query(min_length=1), omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    query = q.lower()
    results = []
    for record in omnigraph.export_branch("main"):
        if "type" not in record:
            continue
        data = record.get("data") or {}
        searchable = " ".join(str(value) for value in data.values() if value is not None)
        if query in searchable.lower():
            results.append(
                {
                    "node_type": record["type"],
                    "slug": data.get("slug"),
                    "matched_text": searchable[:500],
                    "visibility": data.get("visibility"),
                    "provenance": {
                        "source_document_id": data.get("source_document_id"),
                        "source_file": data.get("source_file"),
                        "source_excerpt": data.get("source_excerpt"),
                    },
                }
            )
    return sorted(results, key=lambda item: (item["node_type"], item["slug"] or ""))
