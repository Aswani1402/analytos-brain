from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..config import ApiSettings
from ..database import connect
from ..dependencies import get_omnigraph_service, get_settings
from ..services.omnigraph_service import OmnigraphService

router = APIRouter()


@router.get("/health")
def health(settings: ApiSettings = Depends(get_settings), omnigraph: OmnigraphService = Depends(get_omnigraph_service)):
    sqlite_status = {"ok": False, "path": str(settings.database_path)}
    try:
        with connect(settings.database_path) as connection:
            connection.execute("select 1").fetchone()
        sqlite_status["ok"] = True
    except sqlite3.Error as exc:
        sqlite_status["error"] = str(exc)

    graph_status = {"ok": False, "graph_uri": settings.graph_uri}
    try:
        graph_status.update({"ok": True, "version": omnigraph.version(), "branches": omnigraph.list_branches()})
    except Exception as exc:
        graph_status["error"] = str(exc)
    return {"api": {"ok": True, "name": "analytos-brain-api"}, "sqlite": sqlite_status, "omnigraph": graph_status}
