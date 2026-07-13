from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .canonicalizer import dedupe_payload
from .config import load_settings
from .document_reader import read_document
from .edge_endpoints import ensure_edge_endpoints
from .extractor import build_extractor
from .id_generator import extraction_run_slug, ingestion_branch
from .jsonl_writer import write_jsonl
from .models import ExtractionPayload, ExtractionRun, GraphEdge, SourceDocument
from .omnigraph_loader import OmnigraphLoader


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_run_metadata(payload: ExtractionPayload, document, branch_name: str, model_name: str, prompt_version: str) -> ExtractionPayload:
    now = utc_now()
    source_document = SourceDocument(
        slug=document.slug,
        file_name=document.file_name,
        document_type=document.document_type,
        title=document.title,
        content_hash=document.content_hash,
        source_document_id=document.slug,
        source_file=document.file_name,
        source_excerpt=document.title,
        confidence="1.00",
        visibility="internal",
        created_at=now,
        updated_at=now,
    )
    extraction_run = ExtractionRun(
        slug=extraction_run_slug(branch_name),
        branch_name=branch_name,
        model_name=model_name,
        prompt_version=prompt_version,
        status="pending_review",
        started_at=now,
        completed_at=now,
        source_count="1",
        source_document_id=document.slug,
        source_file=document.file_name,
        source_excerpt=document.title,
        confidence="1.00",
        visibility="internal",
        created_at=now,
        updated_at=now,
    )
    processed = GraphEdge.model_validate(
        {
            "edge": "Processed",
            "from": extraction_run.slug,
            "to": source_document.slug,
            "source_document_id": document.slug,
            "source_file": document.file_name,
            "source_excerpt": document.title,
            "confidence": "1.00",
            "created_at": now,
        }
    )
    return dedupe_payload(
        ExtractionPayload(
            nodes=[source_document, extraction_run, *payload.nodes],
            edges=[processed, *payload.edges],
        )
    )


def ingest_document(path: str | Path, dry_run: bool = False) -> dict:
    settings = load_settings()
    document = read_document(path)
    branch_name = ingestion_branch(document.path, document.content_hash)
    extractor = build_extractor(
        settings.extraction_provider,
        settings.llm_provider,
        settings.llm_model,
        settings.llm_api_key,
    )
    loader = OmnigraphLoader(settings.omnigraph_bin, settings.graph_uri, settings.actor)
    existing_nodes = {}
    if not dry_run:
        existing_nodes = loader.export_nodes("main", ["Product", "Feature"])
    payload = add_run_metadata(
        extractor.extract(document),
        document,
        branch_name,
        extractor.model_name,
        settings.prompt_version,
    )
    payload = dedupe_payload(ensure_edge_endpoints(payload, existing_nodes=existing_nodes))
    output_path = settings.ingest_output_dir / f"{branch_name.replace('/', '__')}.jsonl"
    write_jsonl(payload, output_path)

    load_result = None
    if not dry_run:
        loader.create_branch(branch_name, from_branch="main")
        load_result = loader.load_jsonl(branch_name, output_path)

    return {
        "branch_name": branch_name,
        "jsonl_path": str(output_path),
        "source_document": {
            "file_name": document.file_name,
            "content_hash": document.content_hash,
            "slug": document.slug,
        },
        "review_summary": payload.review_summary(),
        "loaded": not dry_run,
        "load_result": asdict(load_result) if load_result else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a source document into an Omnigraph ingestion branch.")
    parser.add_argument("document", help="Path to a seed/source document")
    parser.add_argument("--dry-run", action="store_true", help="Generate JSONL without creating/loading a branch")
    args = parser.parse_args()
    result = ingest_document(args.document, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
