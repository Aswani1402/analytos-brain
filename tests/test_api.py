from __future__ import annotations

import json
import sqlite3
import subprocess
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app


OMNIGRAPH = Path.home() / ".local" / "bin" / "omnigraph.exe"


@pytest.fixture()
def api_client(tmp_path, monkeypatch):
    if not OMNIGRAPH.exists():
        pytest.skip("Omnigraph CLI is not installed")
    graph = tmp_path.parent / f"api-{uuid.uuid4().hex[:8]}.omni"
    _run_omnigraph(["init", "--schema", "omnigraph/schema.pg", str(graph)])
    db_path = tmp_path / "workflow.db"
    ingestion_dir = tmp_path / "ingestion"
    monkeypatch.setenv("ANALYTOS_REPO_ROOT", str(Path.cwd()))
    monkeypatch.setenv("ANALYTOS_DB_PATH", str(db_path))
    monkeypatch.setenv("OMNIGRAPH_GRAPH_URI", str(graph))
    monkeypatch.setenv("OMNIGRAPH_BIN", str(OMNIGRAPH))
    monkeypatch.setenv("INGEST_OUTPUT_DIR", str(ingestion_dir))
    app = create_app()
    with TestClient(app) as client:
        yield client, graph, db_path


def test_health_endpoint(api_client):
    client, _graph, _db = api_client
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["api"]["ok"] is True
    assert body["sqlite"]["ok"] is True
    assert body["omnigraph"]["ok"] is True


def test_valid_ingestion_creates_branch(api_client):
    client, graph, _db = api_client
    run = _ingest_stockly(client)
    assert run["status"] == "pending_review"
    assert run["branch_name"] in _branches(graph)


def test_ingestion_never_changes_main(api_client):
    client, graph, _db = api_client
    _ingest_stockly(client)
    assert _snapshot_rows(graph, "main") == 0


def test_pending_review_listing(api_client):
    client, _graph, _db = api_client
    run = _ingest_stockly(client)
    response = client.get("/reviews")
    assert response.status_code == 200
    assert [item["run_id"] for item in response.json()] == [run["run_id"]]


def test_review_diff_detects_added_nodes_and_edges(api_client):
    client, _graph, _db = api_client
    run = _ingest_stockly(client)
    response = client.get(f"/reviews/{run['run_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["counts"]["nodes"] > 0
    assert body["counts"]["edges"] > 0
    assert body["added_nodes"]
    assert body["added_edges"]


def test_approval_merges_into_main(api_client):
    client, graph, _db = api_client
    run = _ingest_stockly(client)
    response = client.post(f"/reviews/{run['run_id']}/approve", json={"reviewer_actor": "reviewer-aswini"})
    assert response.status_code == 200
    assert _snapshot_rows(graph, "main") > 0


def test_approval_records_reviewer_actor(api_client):
    client, _graph, _db = api_client
    run = _ingest_stockly(client)
    response = client.post(f"/reviews/{run['run_id']}/approve", json={"reviewer_actor": "reviewer-aswini"})
    assert response.status_code == 200
    saved = client.get(f"/ingestions/{run['run_id']}").json()
    assert saved["status"] == "approved"
    assert saved["reviewer_actor"] == "reviewer-aswini"


def test_rejection_deletes_branch(api_client):
    client, graph, _db = api_client
    run = _ingest_stockly(client)
    response = client.post(
        f"/reviews/{run['run_id']}/reject",
        json={"reviewer_actor": "reviewer-aswini", "reason": "not ready"},
    )
    assert response.status_code == 200
    assert run["branch_name"] not in _branches(graph)


def test_rejected_knowledge_never_reaches_main(api_client):
    client, graph, _db = api_client
    run = _ingest_stockly(client)
    client.post(
        f"/reviews/{run['run_id']}/reject",
        json={"reviewer_actor": "reviewer-aswini", "reason": "not ready"},
    )
    assert _snapshot_rows(graph, "main") == 0


def test_ingestion_service_cannot_self_approve(api_client):
    client, _graph, _db = api_client
    run = _ingest_stockly(client, actor="ingestion-service")
    response = client.post(f"/reviews/{run['run_id']}/approve", json={"reviewer_actor": "ingestion-service"})
    assert response.status_code == 403


def test_duplicate_approval_is_rejected(api_client):
    client, _graph, _db = api_client
    run = _ingest_stockly(client)
    assert client.post(f"/reviews/{run['run_id']}/approve", json={"reviewer_actor": "reviewer-aswini"}).status_code == 200
    response = client.post(f"/reviews/{run['run_id']}/approve", json={"reviewer_actor": "reviewer-aswini"})
    assert response.status_code == 409


def test_duplicate_equivalent_business_edge_is_handled_safely(api_client):
    client, _graph, _db = api_client
    first = _ingest_stockly(client, actor="ingestion-one")
    assert client.post(f"/reviews/{first['run_id']}/approve", json={"reviewer_actor": "reviewer-aswini"}).status_code == 200
    second = _ingest_stockly(client, actor="ingestion-two")
    review = client.get(f"/reviews/{second['run_id']}").json()
    main_edge_keys = {("HasFeature", "product:stockly", "feature:stockly:pull-kanban-engine")}
    added_keys = {(edge["edge"], edge["from"], edge["to"]) for edge in review["added_edges"]}
    assert not (main_edge_keys & added_keys)


def test_path_traversal_is_rejected(api_client):
    client, _graph, _db = api_client
    response = client.post(
        "/ingestions",
        json={"source_path": "../seed-data/stockly-product-overview.md", "actor": "ingestion-service"},
    )
    assert response.status_code == 400


def test_entity_endpoints_read_main_only(api_client):
    client, _graph, _db = api_client
    run = _ingest_stockly(client)
    assert client.get("/entities/products").json() == []
    client.post(f"/reviews/{run['run_id']}/approve", json={"reviewer_actor": "reviewer-aswini"})
    assert client.get("/entities/products").json()


def test_pending_branch_knowledge_is_invisible_to_entity_endpoints(api_client):
    client, _graph, _db = api_client
    _ingest_stockly(client)
    assert client.get("/entities/features").json() == []
    assert client.get("/search", params={"q": "Stockly"}).json() == []


def test_product_detail_works_with_partial_relationships(api_client):
    client, graph, _db = api_client
    data_path = graph.parent / "partial.jsonl"
    _write_jsonl(
        data_path,
        [
            _product_record("product:partial", "Partial Product"),
            _feature_record("feature:partial:one", "Partial Feature"),
            {"edge": "HasFeature", "from": "product:partial", "to": "feature:partial:one", "data": {}},
        ],
    )
    _run_omnigraph(["--as", "pytest", "load", str(graph), "--data", str(data_path), "--mode", "merge", "--branch", "main"])
    response = client.get("/entities/products/product:partial")
    assert response.status_code == 200
    body = response.json()
    assert body["product"]
    assert len(body["features"]) == 1
    assert body["proof_points"] == []
    assert body["icp_segments"] == []


def test_sqlite_contains_workflow_metadata_only(api_client):
    client, _graph, db_path = api_client
    _ingest_stockly(client)
    with sqlite3.connect(db_path) as connection:
        tables = {row[0] for row in connection.execute("select name from sqlite_master where type = 'table'")}
    assert {"ingestion_runs", "audit_events"} <= tables
    assert not (tables & {"Product", "Feature", "ProofPoint", "HasFeature"})


def test_api_processes_real_seed_file_with_rule_based_extraction(api_client):
    client, _graph, _db = api_client
    run = _ingest_stockly(client, provider="rule-based")
    assert run["source_path"] == "seed-data/stockly-product-overview.md"
    assert run["summary"]["node:Product"] == 1
    assert run["summary"]["edge:HasFeature"] == 6


def _ingest_stockly(client: TestClient, actor: str = "ingestion-service", provider: str = "rule-based") -> dict:
    response = client.post(
        "/ingestions",
        json={
            "source_path": "seed-data/stockly-product-overview.md",
            "actor": actor,
            "extraction_provider": provider,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _run_omnigraph(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(OMNIGRAPH), *args], text=True, capture_output=True, check=True)


def _branches(graph: Path) -> list[str]:
    result = _run_omnigraph(["branch", "list", "--store", str(graph)])
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _snapshot_rows(graph: Path, branch: str) -> int:
    result = _run_omnigraph(["snapshot", "--branch", branch, "--store", str(graph)])
    total = 0
    for line in result.stdout.splitlines():
        if " rows=" in line:
            total += int(line.rsplit("rows=", 1)[1])
    return total


def _write_jsonl(path: Path, records: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    return path


def _product_record(slug: str, name: str) -> dict:
    return {"type": "Product", "data": {"id": slug, "slug": slug, "name": name, "status": "active", "visibility": "internal"}}


def _feature_record(slug: str, name: str) -> dict:
    return {"type": "Feature", "data": {"id": slug, "slug": slug, "name": name, "feature_type": "capability", "status": "active", "visibility": "internal"}}
