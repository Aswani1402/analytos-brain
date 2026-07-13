# Demo Script

Start API:

```powershell
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

Start dashboard:

```powershell
Set-Location apps\dashboard
npm run dev -- --host 127.0.0.1
```

Run governed five-document helper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\five_document_flow.ps1
```

The helper ingests the five seed documents, lists pending reviews, inspects
diffs, approves with reviewer attribution, and calls both agents. It does not
reset the real graph.

## Real Local Verification

Backup created before the real run:

```powershell
.tmp\real-graph-backups\20260713-171423
```

Documented reset approach:

```powershell
# Stop API/MCP processes first.
# Move the current runtime graph/data aside, then restore the backup copy.
# Do not delete seed-data, schema, queries, policies, or source files.
```

Run:

```powershell
python scripts\real_local_verification.py
```

Verified result:

- five seed documents ingested through `POST /ingestions`
- five review diffs inspected
- five runs approved by `reviewer-demo`
- main contains Product, Feature, ProofPoint, Persona, ICPSegment, Person, EmailThread, Decision, SourceDocument, and ExtractionRun records
- one unchanged Stockly document re-ingested; repeat diff added only one ExtractionRun and one Processed edge
- sanitized outputs saved under `docs/demo-output/`
