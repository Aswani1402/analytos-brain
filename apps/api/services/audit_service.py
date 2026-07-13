from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..database import connect, rows_to_dicts


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditService:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def record(self, run_id: str | None, actor: str, action: str, details: dict[str, Any]) -> None:
        with connect(self.database_path) as connection:
            connection.execute(
                """
                insert into audit_events (run_id, actor, action, created_at, details_json)
                values (?, ?, ?, ?, ?)
                """,
                (run_id, actor, action, utc_now(), json.dumps(details, sort_keys=True)),
            )

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with connect(self.database_path) as connection:
            rows = connection.execute(
                """
                select id, run_id, actor, action, created_at, details_json
                from audit_events
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        events = rows_to_dicts(rows)
        for event in events:
            event["details"] = json.loads(event.pop("details_json"))
        return events
