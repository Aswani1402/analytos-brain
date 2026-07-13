from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from apps.api.access_control import is_allowed_node, require_allowed
from apps.api.config import load_api_settings
from apps.api.services.omnigraph_service import OmnigraphService


TOOL_NAMES = {
    "search_context",
    "get_product",
    "get_product_features",
    "get_product_proof_points",
    "get_icp_segments",
    "get_personas",
    "get_recent_changes",
    "list_pending_reviews",
    "get_review_diff",
}


def build_omnigraph() -> OmnigraphService:
    settings = load_api_settings()
    return OmnigraphService(settings.omnigraph_bin, settings.graph_uri, settings.query_file, timeout_seconds=settings.command_timeout_seconds)


def call_tool(name: str, arguments: dict[str, Any], omnigraph: OmnigraphService | None = None) -> dict[str, Any]:
    if name not in TOOL_NAMES:
        return {"error": f"Unknown MCP tool: {name}"}
    omnigraph = omnigraph or build_omnigraph()
    actor = str(arguments.get("actor") or "dashboard-reader")
    if name in {"list_pending_reviews", "get_review_diff"}:
        require_allowed(actor, "read_review_diff", branch=str(arguments.get("branch") or "ingestion"))
        return {"error": "Reviewer MCP tools require the FastAPI workflow database and are documented but not exposed by this thin stdio wrapper."}
    if name == "get_recent_changes":
        require_allowed(actor, "read_main", branch="main")
        return {"commits": omnigraph.list_commits(branch="main")}
    if name == "search_context":
        query = str(arguments.get("query") or "").lower()
        records = [_safe_record(actor, record) for record in omnigraph.export_branch("main") if "type" in record]
        records = [record for record in records if record and query in json.dumps(record, sort_keys=True).lower()]
        return {"records": records[:25]}
    if name == "get_product":
        slug = str(arguments.get("slug") or "")
        records = [_safe_record(actor, record) for record in omnigraph.export_branch("main", type_name="Product")]
        return {"records": [record for record in records if record and (record.get("data") or {}).get("slug") == slug]}
    if name == "get_product_features":
        return _records_by_type(actor, omnigraph, "Feature")
    if name == "get_product_proof_points":
        return _records_by_type(actor, omnigraph, "ProofPoint")
    if name == "get_icp_segments":
        return _records_by_type(actor, omnigraph, "ICPSegment")
    if name == "get_personas":
        return _records_by_type(actor, omnigraph, "Persona")
    return {"error": f"Unhandled MCP tool: {name}"}


def _records_by_type(actor: str, omnigraph: OmnigraphService, type_name: str) -> dict[str, Any]:
    records = [_safe_record(actor, record) for record in omnigraph.export_branch("main", type_name=type_name)]
    return {"records": [record for record in records if record]}


def _safe_record(actor: str, record: dict[str, Any]) -> dict[str, Any] | None:
    if not is_allowed_node(actor, record, branch="main"):
        return None
    return record


def stdio_loop() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            result = call_tool(str(request.get("tool")), dict(request.get("arguments") or {}))
            print(json.dumps({"id": request.get("id"), "result": result}, sort_keys=True), flush=True)
        except Exception as exc:
            print(json.dumps({"error": str(exc)}, sort_keys=True), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Thin Analytos Brain MCP-style stdio tool wrapper.")
    parser.add_argument("--once", help="Run one tool call as JSON and exit")
    parser.add_argument("--tool", help="Run one tool call by name and exit")
    parser.add_argument("--actor", default="dashboard-reader")
    parser.add_argument("--query", default="")
    parser.add_argument("--slug", default="")
    args = parser.parse_args()
    if args.once:
        request = json.loads(args.once)
        print(json.dumps(call_tool(str(request["tool"]), dict(request.get("arguments") or {})), indent=2, sort_keys=True))
    elif args.tool:
        arguments = {"actor": args.actor}
        if args.query:
            arguments["query"] = args.query
        if args.slug:
            arguments["slug"] = args.slug
        print(json.dumps(call_tool(args.tool, arguments), indent=2, sort_keys=True))
    else:
        stdio_loop()


if __name__ == "__main__":
    main()
