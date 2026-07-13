from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def post(base_url: str, token: str, payload: dict):
    req = urllib.request.Request(
        base_url.rstrip("/") + "/mcp",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test hosted Analytos MCP Streamable HTTP endpoint.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()

    calls = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search_context", "arguments": {"query": "Stockly"}}},
    ]
    results = [post(args.base_url, args.token, call) for call in calls]
    print(json.dumps({"results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
