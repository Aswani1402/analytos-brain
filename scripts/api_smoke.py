from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TMP = Path(tempfile.gettempdir()) / f"analytos-api-smoke-{uuid.uuid4().hex[:8]}"
PORT = 8018
BASE = f"http://127.0.0.1:{PORT}"
SEEDS = [
    "seed-data/stockly-product-overview.md",
    "seed-data/inspectly-product-overview.md",
    "seed-data/icp-analytos.md",
    "seed-data/email-01-stockly-pilot-thread.md",
    "seed-data/email-02-inspectly-medical-thread.md",
]


def request(path: str, method: str = "GET", payload: dict | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8")
        except Exception as read_error:
            body = json.dumps({"error": f"failed to read error body: {read_error}"})
        return exc.code, json.loads(body) if body else {}


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    graph = TMP / "knowledge.omni"
    db = TMP / "workflow.db"
    ingest = TMP / "ingestion"
    omnigraph = Path.home() / ".local" / "bin" / "omnigraph.exe"
    if not graph.exists():
        subprocess.run([str(omnigraph), "init", "--schema", "omnigraph/schema.pg", str(graph)], cwd=ROOT, check=True)

    env = os.environ.copy()
    env.update(
        {
            "ANALYTOS_DB_PATH": str(db),
            "OMNIGRAPH_GRAPH_URI": str(graph),
            "INGEST_OUTPUT_DIR": str(ingest),
            "OMNIGRAPH_BIN": str(omnigraph),
        }
    )
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    failed = False
    try:
        for _ in range(30):
            try:
                status, health = request("/health")
                if status == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("API did not become ready")

        runs = []
        for seed in SEEDS:
            status, run = request(
                "/ingestions",
                "POST",
                {"source_path": seed, "actor": "ingestion-service", "extraction_provider": "rule-based"},
            )
            if status != 200:
                failed = True
                raise RuntimeError(f"Ingestion failed for {seed}: {status} {run}")
            runs.append(run)

        status, pending = request("/reviews")
        if status != 200 or len(pending) < 5:
            raise RuntimeError(f"Expected at least five pending reviews, got {status} {pending}")

        approved = []
        for run in runs:
            status, diff = request(f"/reviews/{run['run_id']}")
            if status != 200:
                raise RuntimeError(f"Diff failed for {run['run_id']}: {status} {diff}")
            status, result = request(f"/reviews/{run['run_id']}/approve", "POST", {"reviewer_actor": "reviewer-aswini"})
            if status != 200:
                failed = True
                raise RuntimeError(f"Approval failed for {run['run_id']}: {status} {result}")
            approved.append(result["run"])

        content_status, content = request(
            "/agents/content",
            "POST",
            {"topic": "reducing manufacturing inventory", "actor": "content-agent"},
        )
        gtm_status, gtm = request("/agents/gtm", "POST", {"product": "Stockly", "actor": "gtm-agent"})
        denial_status, denial = request(
            "/agents/content",
            "POST",
            {"topic": "email thread", "actor": "dashboard-reader"},
        )
        if denial_status != 403:
            raise RuntimeError(f"Expected dashboard-reader denial for Content Agent, got {denial_status} {denial}")
        print(
            json.dumps(
                {
                    "health": health,
                    "runs": len(runs),
                    "approved": len(approved),
                    "content_status": content_status,
                    "content_facts": len(content.get("facts_used", [])) if isinstance(content, dict) else 0,
                    "gtm_status": gtm_status,
                    "gtm_proofs": len(gtm.get("approved_proof_points_used", [])) if isinstance(gtm, dict) else 0,
                    "denial_status": denial_status,
                    "denial": denial,
                },
                indent=2,
                sort_keys=True,
            )
        )
    finally:
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=10)
        if failed:
            print("UVICORN STDOUT:")
            print(stdout)
            print("UVICORN STDERR:")
            print(stderr)


if __name__ == "__main__":
    main()
