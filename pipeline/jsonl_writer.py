from __future__ import annotations

import json
from pathlib import Path

from .edge_endpoints import ensure_edge_endpoints
from .models import ExtractionPayload


def write_jsonl(payload: ExtractionPayload, path: str | Path) -> Path:
    payload = ensure_edge_endpoints(payload)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for node in payload.nodes:
            handle.write(json.dumps(node.to_omnigraph(), ensure_ascii=False, sort_keys=True) + "\n")
        for edge in payload.edges:
            handle.write(json.dumps(edge.to_omnigraph(), ensure_ascii=False, sort_keys=True) + "\n")
    return output_path
