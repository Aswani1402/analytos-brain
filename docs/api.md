# Analytos Brain API

## Setup

Install dependencies in the active Python environment:

```powershell
python -m pip install -r requirements.txt
```

The backend reads these environment variables when present:

- `OMNIGRAPH_BIN`: path to `omnigraph.exe`
- `OMNIGRAPH_GRAPH_URI`: graph store path, defaults to `omnigraph/graphs/knowledge.omni`
- `ANALYTOS_DB_PATH`: SQLite workflow database path, defaults to `data/analytos_brain.db`
- `INGEST_OUTPUT_DIR`: JSONL ingestion output directory, defaults to `data/ingestion`
- `PROMPT_VERSION`: extraction prompt version, defaults to `v1`

`data/` is ignored by Git and is used for local workflow state and generated ingestion JSONL.

## Startup

```powershell
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

OpenAPI:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/openapi.json
```

## Endpoint List

- `GET /health`
- `POST /ingestions`
- `GET /ingestions`
- `GET /ingestions/{run_id}`
- `GET /reviews`
- `GET /reviews/{run_id}`
- `POST /reviews/{run_id}/approve`
- `POST /reviews/{run_id}/reject`
- `GET /entities/products`
- `GET /entities/products/{slug}`
- `GET /entities/features`
- `GET /entities/proof-points`
- `GET /entities/icp-segments`
- `GET /entities/personas`
- `GET /entities/people`
- `GET /entities/email-threads`
- `GET /entities/decisions`
- `GET /search?q=<text>`
- `GET /changes/recent`

## Ingestion Request

```json
{
  "source_path": "seed-data/stockly-product-overview.md",
  "actor": "ingestion-service",
  "extraction_provider": "rule-based"
}
```

Example response:

```json
{
  "run_id": "run-abc123",
  "source_path": "seed-data/stockly-product-overview.md",
  "source_document_hash": "d802a84c760a...",
  "branch_name": "ing-20260713091530012345-stockly-prod-d802a84c-abc123def456",
  "status": "pending_review",
  "summary": {
    "nodes": 11,
    "edges": 10,
    "node:Product": 1,
    "edge:HasFeature": 6
  },
  "review_url": "/reviews/run-abc123"
}
```

Ingestion always creates a separate branch from `main` and loads JSONL into that branch only.

## Review Flow

`GET /reviews` lists pending runs. `GET /reviews/{run_id}` returns source document text, branch name, added/changed/removed nodes, added/changed/removed edges, counts, confidence, provenance, and visibility summaries.

The diff is computed by exporting `main` and the ingestion branch as JSONL. Internal Omnigraph `id` fields are ignored. Node keys are `type + slug`; edge keys are `edge + from + to`.

## Approval Flow

```json
{
  "reviewer_actor": "reviewer-aswini"
}
```

Approval requires `pending_review` status, a live ingestion branch, and a reviewer different from the ingestion actor. The API recalculates the diff immediately before approval, validates unsafe records, checks duplicate business edges, merges the branch into `main`, and records reviewer metadata in SQLite.

## Rejection Flow

```json
{
  "reviewer_actor": "reviewer-aswini",
  "reason": "Rejected because the extraction needs correction."
}
```

Rejection requires `pending_review` status. The API deletes the ingestion branch, marks the run rejected, and records the reviewer, reviewed time, and reason.

## Status Transitions

- `extracting`: reserved for future async workers
- `pending_review`: ingestion branch created and loaded
- `approved`: branch merged to `main`
- `rejected`: branch deleted or discarded
- `failed`: extraction, validation, branch creation, or branch load failed

Only `pending_review` runs can be approved or rejected.

## SQLite Purpose

SQLite stores workflow state only:

- ingestion run ID
- source document path and hash
- branch name
- extraction provider and model
- ingestion actor
- status
- created/reviewed timestamps
- reviewer actor
- rejection reason
- merge result
- audit events

SQLite does not store graph entities, graph edges, or approved company knowledge.

## Graph/Main Safety

Entity, search, and product-detail endpoints read approved `main` only. Pending branches are not searched or exposed through entity endpoints. Ingestion never writes directly to `main`; only approval merges a reviewed branch into `main`.

## Common Errors

- `400 Source path is not in an allowed directory`: source path is outside `seed-data/` or the configured upload directory.
- `400 Invalid actor identifier`: actor contains unsupported characters.
- `403 The ingestion actor cannot approve its own branch`: self-approval is blocked.
- `409 Only pending_review runs can be approved`: the run was already approved, rejected, or failed.
- `409 Ingestion branch no longer exists`: the branch was deleted outside the API.
- `500 Ingestion failed`: Omnigraph or extraction failed; inspect the run metadata and audit log.
