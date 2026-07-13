from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from pipeline.canonicalizer import dedupe_payload
from pipeline.document_reader import read_document
from pipeline.edge_endpoints import ensure_edge_endpoints
from pipeline.extractor import RuleBasedExtractor
from pipeline.id_generator import ingestion_branch, sha256_text, slugify, source_document_slug
from pipeline.ingest import add_run_metadata
from pipeline.jsonl_writer import write_jsonl
from pipeline.models import ExtractionPayload, Product


def test_slugify_and_hash_are_deterministic():
    assert slugify("Pull Kanban + Monte Carlo") == "pull-kanban-monte-carlo"
    assert sha256_text("same") == sha256_text("same")
    assert sha256_text("same") != sha256_text("different")


def test_source_document_identity_uses_content_hash(tmp_path):
    path = tmp_path / "example.md"
    path.write_text("# Example\ncontent", encoding="utf-8")
    document = read_document(path)
    assert document.content_hash == sha256_text("# Example\ncontent")
    assert document.slug == source_document_slug(path, document.content_hash)


def test_ingestion_branch_is_unique_but_content_prefix_is_stable(tmp_path):
    path = tmp_path / "stockly-product-overview.md"
    content_hash = sha256_text("content")
    first = ingestion_branch(path, content_hash, datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc))
    second = ingestion_branch(path, content_hash, datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc))
    assert first != second
    assert "ed7002b4" in first
    assert "ed7002b4" in second
    assert "stockly-prod" in first
    assert "stockly-prod" in second
    assert first.startswith("ing-")


def test_many_ingestion_branches_are_unique(tmp_path):
    path = tmp_path / "stockly-product-overview.md"
    content_hash = sha256_text("content")
    branches = {ingestion_branch(path, content_hash) for _ in range(1000)}
    assert len(branches) == 1000
    assert all("stockly-prod" in branch and "ed7002b4" in branch and branch.startswith("ing-") for branch in branches)


def test_product_model_requires_deterministic_slug():
    with pytest.raises(ValidationError):
        Product(slug="stockly", name="Stockly", status="active")


def test_rule_based_extractor_generates_stockly_payload():
    document = read_document("seed-data/stockly-product-overview.md")
    payload = RuleBasedExtractor().extract(document)
    summary = payload.review_summary()
    assert summary["node:Product"] == 1
    assert summary["node:Feature"] == 6
    assert summary["node:ProofPoint"] == 3
    assert summary["edge:HasFeature"] == 6
    assert summary["edge:ProvenBy"] == 3


def test_jsonl_generation_includes_nodes_and_edges(tmp_path):
    document = read_document("seed-data/stockly-product-overview.md")
    payload = add_run_metadata(
        RuleBasedExtractor().extract(document),
        document,
        "ing-20260101000000000000-stockly-product-overview-ed7002b4-000000000001",
        "mock-rule-based-v1",
        "v1",
    )
    output = write_jsonl(payload, tmp_path / "out.jsonl")
    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert any(record.get("type") == "Product" and record["data"]["slug"] == "product:stockly" for record in records)
    assert any(record.get("edge") == "Processed" for record in records)


def test_icp_payload_includes_product_endpoints_without_relationship_loss():
    payload = _payload_for_seed("seed-data/icp-analytos.md")
    assert _edge_count(payload, "Targets") == 4
    assert {node.slug for node in payload.nodes if node.node_type == "Product"} == {"product:stockly", "product:inspectly"}
    _assert_all_edge_endpoints_exist(payload)


def test_stockly_email_payload_includes_product_and_feature_endpoints_without_relationship_loss():
    payload = _payload_for_seed("seed-data/email-01-stockly-pilot-thread.md")
    assert _edge_count(payload, "Discusses") == 1
    assert _edge_count(payload, "SupportedBy") == 1
    assert {"product:stockly", "feature:stockly:supplier-lead-time-intelligence"} <= {node.slug for node in payload.nodes}
    _assert_all_edge_endpoints_exist(payload)


def test_inspectly_email_payload_includes_product_and_feature_endpoints_without_relationship_loss():
    payload = _payload_for_seed("seed-data/email-02-inspectly-medical-thread.md")
    assert _edge_count(payload, "Discusses") == 1
    assert _edge_count(payload, "SupportedBy") == 1
    assert {"product:inspectly", "feature:inspectly:revision-diffing"} <= {node.slug for node in payload.nodes}
    _assert_all_edge_endpoints_exist(payload)


def test_seed_entity_slugs_are_deterministic():
    first = _payload_for_seed("seed-data/email-01-stockly-pilot-thread.md")
    second = _payload_for_seed("seed-data/email-01-stockly-pilot-thread.md")
    assert [node.slug for node in first.nodes] == [node.slug for node in second.nodes]
    assert [(edge.edge, edge.from_slug, edge.to_slug) for edge in first.edges] == [
        (edge.edge, edge.from_slug, edge.to_slug) for edge in second.edges
    ]


def test_dedupe_payload_removes_duplicate_nodes_and_edges():
    document = read_document("seed-data/stockly-product-overview.md")
    payload = RuleBasedExtractor().extract(document)
    duplicated = ExtractionPayload(nodes=[*payload.nodes, *payload.nodes], edges=[*payload.edges, *payload.edges])
    deduped = dedupe_payload(duplicated)
    assert len(deduped.nodes) == len(payload.nodes)
    assert len(deduped.edges) == len(payload.edges)


def test_icp_ingestion_loads_into_empty_omnigraph_graph(tmp_path):
    _assert_seed_loads_into_empty_graph(tmp_path, "seed-data/icp-analytos.md")


def test_stockly_email_ingestion_loads_into_empty_omnigraph_graph(tmp_path):
    _assert_seed_loads_into_empty_graph(tmp_path, "seed-data/email-01-stockly-pilot-thread.md")


def test_inspectly_email_ingestion_loads_into_empty_omnigraph_graph(tmp_path):
    _assert_seed_loads_into_empty_graph(tmp_path, "seed-data/email-02-inspectly-medical-thread.md")


def test_repeated_document_ingestion_uses_unique_branches_with_same_business_payload(tmp_path):
    document = read_document("seed-data/email-01-stockly-pilot-thread.md")
    first_branch = ingestion_branch(document.path, document.content_hash)
    second_branch = ingestion_branch(document.path, document.content_hash)
    first_payload = dedupe_payload(
        ensure_edge_endpoints(
            add_run_metadata(RuleBasedExtractor().extract(document), document, first_branch, "mock-rule-based-v1", "v1")
        )
    )
    second_payload = dedupe_payload(
        ensure_edge_endpoints(
            add_run_metadata(RuleBasedExtractor().extract(document), document, second_branch, "mock-rule-based-v1", "v1")
        )
    )
    assert first_branch != second_branch
    assert _business_signature(first_payload) == _business_signature(second_payload)

    first_jsonl = write_jsonl(first_payload, tmp_path / "stockly-email-first.jsonl")
    second_jsonl = write_jsonl(second_payload, tmp_path / "stockly-email-second.jsonl")
    graph = _init_temp_graph(tmp_path)
    _run_omnigraph(["branch", "create", first_branch, "--uri", str(graph), "--from", "main"])
    _run_omnigraph(["branch", "create", second_branch, "--uri", str(graph), "--from", "main"])
    _run_omnigraph(["--as", "pytest", "load", str(graph), "--data", str(first_jsonl), "--mode", "merge", "--branch", first_branch])
    _run_omnigraph(["--as", "pytest", "load", str(graph), "--data", str(second_jsonl), "--mode", "merge", "--branch", second_branch])


def test_omnigraph_merge_clears_omitted_optional_fields(tmp_path):
    graph = _init_temp_graph(tmp_path)
    rich = tmp_path / "rich.jsonl"
    minimal = tmp_path / "minimal.jsonl"
    rich.write_text(
        json.dumps(
            {
                "type": "Product",
                "data": {
                    "id": "product:merge-probe",
                    "slug": "product:merge-probe",
                    "name": "Merge Probe",
                    "site_url": "probe.example",
                    "category": "Rich category",
                    "owner": "Owner",
                    "status": "active",
                    "summary": "Rich summary",
                    "visibility": "internal",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    minimal.write_text(
        json.dumps(
            {
                "type": "Product",
                "data": {
                    "id": "product:merge-probe",
                    "slug": "product:merge-probe",
                    "name": "Merge Probe",
                    "status": "active",
                    "visibility": "internal",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _run_omnigraph(["--as", "pytest", "load", str(graph), "--data", str(rich), "--mode", "merge", "--branch", "main"])
    _run_omnigraph(["--as", "pytest", "load", str(graph), "--data", str(minimal), "--mode", "merge", "--branch", "main"])
    exported = _run_omnigraph(["export", str(graph), "--branch", "main", "--type", "Product"]).stdout
    record = json.loads(exported)
    assert record["data"]["site_url"] is None
    assert record["data"]["category"] is None
    assert record["data"]["owner"] is None
    assert record["data"]["summary"] is None


def test_product_with_only_features_can_be_retrieved(tmp_path):
    graph = _init_temp_graph(tmp_path)
    jsonl_path = _write_records(
        tmp_path / "features-only.jsonl",
        [
            _product_record("product:partial-feature", "Partial Feature Product"),
            _feature_record("feature:partial-feature:one", "Only Feature"),
            {"edge": "HasFeature", "from": "product:partial-feature", "to": "feature:partial-feature:one", "data": {}},
        ],
    )
    _run_omnigraph(["--as", "pytest", "load", str(graph), "--data", str(jsonl_path), "--mode", "merge", "--branch", "main"])

    product_rows = _query_records(graph, "get_product", "product:partial-feature")
    feature_rows = _query_records(graph, "get_product_features", "product:partial-feature")
    proof_rows = _query_records(graph, "get_product_proof_points", "product:partial-feature")
    icp_rows = _query_records(graph, "get_product_icp_segments", "product:partial-feature")

    assert len(product_rows) == 1
    assert len(feature_rows) == 1
    assert proof_rows == []
    assert icp_rows == []


def test_product_with_features_and_proof_but_no_icp_can_be_retrieved(tmp_path):
    graph = _init_temp_graph(tmp_path)
    jsonl_path = _write_records(
        tmp_path / "features-proof.jsonl",
        [
            _product_record("product:partial-proof", "Partial Proof Product"),
            _feature_record("feature:partial-proof:one", "Feature One"),
            _proof_record("proof:partial-proof:one", "Proof One"),
            {"edge": "HasFeature", "from": "product:partial-proof", "to": "feature:partial-proof:one", "data": {}},
            {"edge": "ProvenBy", "from": "product:partial-proof", "to": "proof:partial-proof:one", "data": {}},
        ],
    )
    _run_omnigraph(["--as", "pytest", "load", str(graph), "--data", str(jsonl_path), "--mode", "merge", "--branch", "main"])

    assert len(_query_records(graph, "get_product", "product:partial-proof")) == 1
    assert len(_query_records(graph, "get_product_features", "product:partial-proof")) == 1
    assert len(_query_records(graph, "get_product_proof_points", "product:partial-proof")) == 1
    assert _query_records(graph, "get_product_icp_segments", "product:partial-proof") == []


def test_fully_connected_product_returns_all_context_parts(tmp_path):
    graph = _init_temp_graph(tmp_path)
    jsonl_path = _write_records(
        tmp_path / "full-context.jsonl",
        [
            _product_record("product:full-context", "Full Context Product"),
            _feature_record("feature:full-context:one", "Feature One"),
            _proof_record("proof:full-context:one", "Proof One"),
            _icp_record("icp:full-context", "Full Context ICP"),
            {"edge": "HasFeature", "from": "product:full-context", "to": "feature:full-context:one", "data": {}},
            {"edge": "ProvenBy", "from": "product:full-context", "to": "proof:full-context:one", "data": {}},
            {"edge": "Targets", "from": "product:full-context", "to": "icp:full-context", "data": {}},
        ],
    )
    _run_omnigraph(["--as", "pytest", "load", str(graph), "--data", str(jsonl_path), "--mode", "merge", "--branch", "main"])

    assert len(_query_records(graph, "get_product", "product:full-context")) == 1
    assert len(_query_records(graph, "get_product_features", "product:full-context")) == 1
    assert len(_query_records(graph, "get_product_proof_points", "product:full-context")) == 1
    assert len(_query_records(graph, "get_product_icp_segments", "product:full-context")) == 1


def _payload_for_seed(path: str) -> ExtractionPayload:
    document = read_document(path)
    payload = add_run_metadata(
        RuleBasedExtractor().extract(document),
        document,
        "ing-20260101000000000000-seed-document-ed7002b4-000000000001",
        "mock-rule-based-v1",
        "v1",
    )
    return dedupe_payload(ensure_edge_endpoints(payload))


def _edge_count(payload: ExtractionPayload, edge_name: str) -> int:
    return sum(1 for edge in payload.edges if edge.edge == edge_name)


def _assert_all_edge_endpoints_exist(payload: ExtractionPayload) -> None:
    slugs = {node.slug for node in payload.nodes}
    missing = [
        (edge.edge, edge.from_slug, edge.to_slug)
        for edge in payload.edges
        if edge.from_slug not in slugs or edge.to_slug not in slugs
    ]
    assert missing == []


def _business_signature(payload: ExtractionPayload) -> tuple[tuple[str, ...], tuple[tuple[str, str, str], ...]]:
    node_slugs = tuple(sorted(node.slug for node in payload.nodes if node.node_type not in {"ExtractionRun"}))
    edge_keys = tuple(
        sorted(
            (edge.edge, edge.from_slug, edge.to_slug)
            for edge in payload.edges
            if edge.edge != "Processed"
        )
    )
    return node_slugs, edge_keys


def _assert_seed_loads_into_empty_graph(tmp_path: Path, seed_path: str) -> None:
    payload = _payload_for_seed(seed_path)
    jsonl_path = write_jsonl(payload, tmp_path / f"{Path(seed_path).stem}.jsonl")
    graph = _init_temp_graph(tmp_path)
    _run_omnigraph(["--as", "pytest", "load", str(graph), "--data", str(jsonl_path), "--mode", "merge", "--branch", "main"])


def _init_temp_graph(tmp_path: Path) -> Path:
    graph = tmp_path.parent / f"g-{uuid.uuid4().hex[:8]}.omni"
    graph.parent.mkdir(parents=True, exist_ok=True)
    _run_omnigraph(["init", "--schema", "omnigraph/schema.pg", str(graph)])
    return graph


def _run_omnigraph(args: list[str]) -> subprocess.CompletedProcess[str]:
    binary = Path.home() / ".local" / "bin" / "omnigraph.exe"
    if not binary.exists():
        binary_name = shutil.which("omnigraph")
        if binary_name is None:
            pytest.skip("Omnigraph CLI is not installed")
        binary = Path(binary_name)
    return subprocess.run([str(binary), *args], text=True, capture_output=True, check=True)


def _write_records(path: Path, records: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    return path


def _product_record(slug: str, name: str) -> dict:
    return {
        "type": "Product",
        "data": {
            "id": slug,
            "slug": slug,
            "name": name,
            "status": "active",
            "visibility": "internal",
        },
    }


def _feature_record(slug: str, name: str) -> dict:
    return {
        "type": "Feature",
        "data": {
            "id": slug,
            "slug": slug,
            "name": name,
            "feature_type": "capability",
            "status": "active",
            "visibility": "internal",
        },
    }


def _proof_record(slug: str, name: str) -> dict:
    return {
        "type": "ProofPoint",
        "data": {
            "id": slug,
            "slug": slug,
            "name": name,
            "proof_type": "metric",
            "approved_for_external_use": "false",
            "visibility": "internal",
        },
    }


def _icp_record(slug: str, name: str) -> dict:
    return {
        "type": "ICPSegment",
        "data": {
            "id": slug,
            "slug": slug,
            "name": name,
            "segment_type": "direct",
            "status": "active",
            "visibility": "internal",
        },
    }


def _query_records(graph: Path, query_name: str, product_slug: str) -> list[dict]:
    result = _run_omnigraph(
        [
            "query",
            query_name,
            "--query",
            "omnigraph/queries/products.gq",
            "--store",
            str(graph),
            "--branch",
            "main",
            "--params",
            json.dumps({"product_slug": product_slug}),
            "--format",
            "jsonl",
        ]
    )
    records = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    return [record for record in records if record.get("kind") != "metadata"]
