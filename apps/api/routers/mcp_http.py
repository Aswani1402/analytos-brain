from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException

from mcp.server import TOOL_NAMES, call_tool

from ..auth import mcp_actor_from_authorization
from ..dependencies import get_omnigraph_service
from ..services.omnigraph_service import OmnigraphService

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("")
def mcp_health():
    return {"ok": True, "transport": "streamable-http", "protocol": "json-rpc-2.0"}


@router.post("")
def mcp_rpc(
    request: dict[str, Any],
    authorization: Annotated[str | None, Header()] = None,
    omnigraph: OmnigraphService = Depends(get_omnigraph_service),
):
    actor = mcp_actor_from_authorization(authorization)
    method = str(request.get("method") or "")
    request_id = request.get("id")
    params = request.get("params") if isinstance(request.get("params"), dict) else {}
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "analytos-brain", "version": "0.1.0"},
                "capabilities": {"tools": {"listChanged": False}},
            }
        elif method == "tools/list":
            result = {"tools": [_tool_descriptor(name) for name in sorted(_hosted_tool_names())]}
        elif method == "tools/call":
            name = str(params.get("name") or "")
            arguments = dict(params.get("arguments") or {})
            arguments["actor"] = actor
            result = {"content": [{"type": "text", "text": _json_text(call_tool(name, arguments, omnigraph))}]}
        else:
            return _error(request_id, -32601, "Method not found")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except HTTPException:
        raise
    except Exception as exc:
        return _error(request_id, -32000, str(exc))


def _hosted_tool_names() -> set[str]:
    return TOOL_NAMES - {"list_pending_reviews", "get_review_diff"}


def _tool_descriptor(name: str) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    if name == "search_context":
        properties["query"] = {"type": "string"}
        required.append("query")
    if name == "get_product":
        properties["slug"] = {"type": "string"}
        required.append("slug")
    return {
        "name": name,
        "description": f"Analytos Brain {name} tool",
        "inputSchema": {"type": "object", "properties": properties, "required": required},
    }


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _json_text(data: Any) -> str:
    import json

    return json.dumps(data, sort_keys=True)
