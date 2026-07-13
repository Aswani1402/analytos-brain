# Architecture

Analytos Brain ingests source documents into isolated Omnigraph branches,
stores workflow state in SQLite, and exposes approved `main` graph knowledge
through FastAPI, React, and a thin MCP wrapper.

Flow:

1. `pipeline.document_reader` hashes and classifies a source file.
2. `pipeline.extractor` produces Pydantic-validated graph nodes and edges.
3. `pipeline.ingest` adds source/run metadata and writes JSONL.
4. `apps.api.services.ingestion_service` creates an ingestion branch and loads JSONL.
5. `apps.api.services.review_service` computes a diff and merges only after approval.
6. Dashboard, agents, and MCP tools read approved `main`.

The default extractor is deterministic. `EXTRACTION_PROVIDER=llm` enables the
Gemini adapter with structured JSON validation.
