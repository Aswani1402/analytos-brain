from __future__ import annotations

import argparse
import json
import urllib.request


SEEDS = [
    "seed-data/stockly-product-overview.md",
    "seed-data/inspectly-product-overview.md",
    "seed-data/icp-analytos.md",
    "seed-data/email-01-stockly-pilot-thread.md",
    "seed-data/email-02-inspectly-medical-thread.md",
]


def request(base_url: str, api_token: str, path: str, method: str = "GET", payload: dict | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate hosted Analytos graph through governed HITL API flow.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-token", required=True)
    parser.add_argument("--reviewer", default="reviewer-demo")
    args = parser.parse_args()

    health_status, health = request(args.base_url, args.api_token, "/health")
    runs = []
    for seed in SEEDS:
        status, run = request(
            args.base_url,
            args.api_token,
            "/ingestions",
            "POST",
            {"source_path": seed, "actor": "ingestion-service", "extraction_provider": "rule-based"},
        )
        if status != 200:
            raise RuntimeError(f"Ingestion failed for {seed}: {status}")
        runs.append(run)
    _, pending = request(args.base_url, args.api_token, "/reviews")
    approvals = []
    for run in runs:
        request(args.base_url, args.api_token, f"/reviews/{run['run_id']}")
        _, approved = request(args.base_url, args.api_token, f"/reviews/{run['run_id']}/approve", "POST", {"reviewer_actor": args.reviewer})
        approvals.append(approved["run"])
    content = request(args.base_url, args.api_token, "/agents/content", "POST", {"topic": "reducing manufacturing inventory", "actor": "content-agent"})[1]
    gtm = request(args.base_url, args.api_token, "/agents/gtm", "POST", {"product": "Stockly", "actor": "gtm-agent"})[1]
    print(json.dumps({"health": health, "pending": len(pending), "approved": len(approvals), "content_facts": len(content.get("facts_used", [])), "gtm_proofs": len(gtm.get("approved_proof_points_used", []))}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
