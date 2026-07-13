from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any


SCHEMA = """
create table if not exists ingestion_runs (
    run_id text primary key,
    source_path text not null,
    source_document_hash text not null,
    branch_name text not null unique,
    extraction_provider text not null,
    extraction_model text not null,
    ingestion_actor text not null default 'unknown',
    status text not null,
    created_at text not null,
    reviewer_actor text,
    reviewed_at text,
    rejection_reason text,
    merge_result text,
    summary_json text not null,
    jsonl_path text not null,
    error_message text
);

create table if not exists audit_events (
    id integer primary key autoincrement,
    run_id text,
    actor text not null,
    action text not null,
    created_at text not null,
    details_json text not null
);
"""


def connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_path: Path) -> None:
    with connect(database_path) as connection:
        connection.executescript(SCHEMA)
        columns = {
            row["name"]
            for row in connection.execute("pragma table_info(ingestion_runs)").fetchall()
        }
        if "ingestion_actor" not in columns:
            connection.execute("alter table ingestion_runs add column ingestion_actor text not null default 'unknown'")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    if data.get("summary_json"):
        data["summary"] = json.loads(data["summary_json"])
    data.pop("summary_json", None)
    if data.get("merge_result"):
        data["merge_result"] = json.loads(data["merge_result"])
    return data


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [row_to_dict(row) or {} for row in rows]
