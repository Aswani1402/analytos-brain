from __future__ import annotations

import json
import os
from typing import Annotated

from fastapi import Header, HTTPException


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def require_api_token(authorization: Annotated[str | None, Header()] = None) -> None:
    expected = os.getenv("ANALYTOS_API_TOKEN", "").strip()
    if not expected:
        return
    if _bearer_token(authorization) != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def mcp_actor_from_authorization(authorization: str | None) -> str:
    mapping = _mcp_token_map()
    if not mapping:
        raise HTTPException(status_code=503, detail="MCP token mapping is not configured")
    token = _bearer_token(authorization)
    actor = mapping.get(token or "")
    if not actor:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return actor


def _mcp_token_map() -> dict[str, str]:
    raw = os.getenv("ANALYTOS_MCP_TOKENS_JSON", "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="MCP token mapping is invalid") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=500, detail="MCP token mapping must be an object")
    return {str(token): str(actor) for token, actor in parsed.items()}
