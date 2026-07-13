from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORT = 8020
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
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def safe_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True)
    text = text.replace("Santosh Thota", "internal-person")
    text = text.replace("Narayan Laksham", "internal-person")
    text = text.replace("Ashok Suthar", "internal-person")
    text = text.replace("santosh@analytos.ai", "internal@example.invalid")
    text = text.replace("narayan@analytos.ai", "internal@example.invalid")
    text = text.replace("ashok@analytos.ai", "internal@example.invalid")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    graph = ROOT / "omnigraph" / "graphs" / "knowledge.omni"
    db = ROOT / "data" / "analytos_brain.db"
    ingest = ROOT / "data" / "ingestion"
    omnigraph = Path.home() / ".local" / "bin" / "omnigraph.exe"

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

        before_snapshot = subprocess.run(
            [str(omnigraph), "snapshot", "--branch", "main", "--store", str(graph)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout

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
        if status != 200:
            failed = True
            raise RuntimeError(f"Pending reviews failed: {status} {pending}")

        branch_list_before = subprocess.run(
            [str(omnigraph), "branch", "list", "--store", str(graph)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.splitlines()

        diffs = []
        approvals = []
        for run in runs:
            status, diff = request(f"/reviews/{run['run_id']}")
            if status != 200:
                failed = True
                raise RuntimeError(f"Diff failed for {run['run_id']}: {status} {diff}")
            diffs.append({"run_id": run["run_id"], "counts": diff.get("counts"), "branch_name": diff.get("branch_name")})
            status, result = request(f"/reviews/{run['run_id']}/approve", "POST", {"reviewer_actor": "reviewer-demo"})
            if status != 200:
                failed = True
                raise RuntimeError(f"Approval failed for {run['run_id']}: {status} {result}")
            approvals.append(result["run"])

        after_snapshot = subprocess.run(
            [str(omnigraph), "snapshot", "--branch", "main", "--store", str(graph)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        commits = subprocess.run(
            [str(omnigraph), "commit", "list", str(graph), "--branch", "main", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        status, content = request(
            "/agents/content",
            "POST",
            {"topic": "reducing manufacturing inventory", "actor": "content-agent"},
        )
        if status != 200:
            failed = True
            raise RuntimeError(f"Content Agent failed: {status} {content}")
        status, gtm = request("/agents/gtm", "POST", {"product": "Stockly", "actor": "gtm-agent"})
        if status != 200:
            failed = True
            raise RuntimeError(f"GTM Agent failed: {status} {gtm}")
        denial_status, denial = request("/agents/content", "POST", {"topic": "email", "actor": "dashboard-reader"})
        if denial_status != 403:
            failed = True
            raise RuntimeError(f"Expected dashboard denial, got {denial_status}: {denial}")

        status, repeat_run = request(
            "/ingestions",
            "POST",
            {"source_path": SEEDS[0], "actor": "ingestion-service", "extraction_provider": "rule-based"},
        )
        if status != 200:
            failed = True
            raise RuntimeError(f"Repeat ingestion failed: {status} {repeat_run}")
        status, repeat_diff = request(f"/reviews/{repeat_run['run_id']}")
        if status != 200:
            failed = True
            raise RuntimeError(f"Repeat diff failed: {status} {repeat_diff}")
        status, repeat_approval = request(f"/reviews/{repeat_run['run_id']}/approve", "POST", {"reviewer_actor": "reviewer-demo"})
        if status != 200:
            failed = True
            raise RuntimeError(f"Repeat approval failed: {status} {repeat_approval}")
        final_snapshot = subprocess.run(
            [str(omnigraph), "snapshot", "--branch", "main", "--store", str(graph)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout

        branch_list_after = subprocess.run(
            [str(omnigraph), "branch", "list", "--store", str(graph)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.splitlines()

        output = {
            "health": health,
            "before_snapshot": before_snapshot,
            "pending_review_count": len(pending),
            "branches_before_approval": branch_list_before,
            "diffs": diffs,
            "approved_runs": [{"run_id": run["run_id"], "reviewer_actor": run.get("reviewer_actor"), "branch_name": run["branch_name"]} for run in approvals],
            "after_snapshot": after_snapshot,
            "repeat_diff_counts": repeat_diff.get("counts"),
            "repeat_approval": {
                "run_id": repeat_approval["run"]["run_id"],
                "reviewer_actor": repeat_approval["run"].get("reviewer_actor"),
                "branch_name": repeat_approval["run"]["branch_name"],
            },
            "final_snapshot": final_snapshot,
            "branches_after_approval": branch_list_after,
            "commit_list": commits.stdout if commits.returncode == 0 else commits.stderr,
            "content_summary": {
                "status": 200,
                "facts_used": len(content.get("facts_used", [])),
                "graph_node_slugs": content.get("graph_node_slugs", []),
                "source_documents": content.get("source_documents", []),
            },
            "gtm_summary": {
                "status": 200,
                "proof_points": len(gtm.get("approved_proof_points_used", [])),
                "graph_node_slugs": gtm.get("graph_node_slugs", []),
                "illustrative_companies": gtm.get("illustrative_companies", []),
            },
            "dashboard_reader_denial": {"status": denial_status, "body": denial},
        }
        safe_json(ROOT / "docs" / "demo-output" / "real-local-verification.json", output)
        safe_json(ROOT / "docs" / "demo-output" / "content-agent-sample.json", content)
        safe_json(ROOT / "docs" / "demo-output" / "gtm-agent-sample.json", gtm)
        print(json.dumps(output, indent=2, sort_keys=True))
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
