from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ApiSettings:
    repo_root: Path
    database_path: Path
    omnigraph_bin: str
    graph_uri: str
    ingest_output_dir: Path
    prompt_version: str
    allowed_upload_dir: Path
    query_file: Path
    cors_origins: tuple[str, ...]
    command_timeout_seconds: int = 30


def load_api_settings() -> ApiSettings:
    repo_root = Path(os.getenv("ANALYTOS_REPO_ROOT", Path.cwd())).resolve()
    database_path = Path(os.getenv("ANALYTOS_DB_PATH", repo_root / "data" / "analytos_brain.db"))
    if not database_path.is_absolute():
        database_path = repo_root / database_path
    graph_uri = os.getenv("OMNIGRAPH_GRAPH_URI", "omnigraph/graphs/knowledge.omni")
    graph_path = Path(graph_uri)
    if not graph_path.is_absolute():
        graph_uri = str(repo_root / graph_path)
    ingest_output_dir = Path(os.getenv("INGEST_OUTPUT_DIR", repo_root / "data" / "ingestion"))
    if not ingest_output_dir.is_absolute():
        ingest_output_dir = repo_root / ingest_output_dir
    allowed_upload_dir = Path(os.getenv("ANALYTOS_UPLOAD_DIR", repo_root / "data" / "uploads"))
    if not allowed_upload_dir.is_absolute():
        allowed_upload_dir = repo_root / allowed_upload_dir
    query_file = Path(os.getenv("ANALYTOS_QUERY_FILE", repo_root / "omnigraph" / "queries" / "products.gq"))
    if not query_file.is_absolute():
        query_file = repo_root / query_file
    return ApiSettings(
        repo_root=repo_root,
        database_path=database_path,
        omnigraph_bin=os.getenv("OMNIGRAPH_BIN", str(Path.home() / ".local" / "bin" / "omnigraph.exe")),
        graph_uri=graph_uri,
        ingest_output_dir=ingest_output_dir,
        prompt_version=os.getenv("PROMPT_VERSION", "v1"),
        allowed_upload_dir=allowed_upload_dir.resolve(),
        query_file=query_file.resolve(),
        cors_origins=tuple(
            origin.strip()
            for origin in os.getenv("ANALYTOS_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
            if origin.strip()
        ),
        command_timeout_seconds=int(os.getenv("OMNIGRAPH_TIMEOUT_SECONDS", "30")),
    )
