from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    omnigraph_bin: str
    graph_uri: str
    actor: str
    ingest_output_dir: Path
    extraction_provider: str
    llm_provider: str
    llm_model: str
    llm_api_key: str
    prompt_version: str


def load_settings() -> Settings:
    return Settings(
        omnigraph_bin=os.getenv("OMNIGRAPH_BIN", str(Path.home() / ".local" / "bin" / "omnigraph.exe")),
        graph_uri=os.getenv("OMNIGRAPH_GRAPH_URI", "omnigraph/graphs/knowledge.omni"),
        actor=os.getenv("OMNIGRAPH_ACTOR", "local-reviewer"),
        ingest_output_dir=Path(os.getenv("INGEST_OUTPUT_DIR", "data/ingestion")),
        extraction_provider=os.getenv("EXTRACTION_PROVIDER", "rule-based"),
        llm_provider=os.getenv("LLM_PROVIDER", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        prompt_version=os.getenv("PROMPT_VERSION", "v1"),
    )
