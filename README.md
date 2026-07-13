Analytos Brain
==============

Current completion status:

- Typed Omnigraph schema and stored read queries are implemented.
- Rule-based seed extraction and branch-isolated ingestion are implemented.
- FastAPI backend for ingestion, HITL review, approval, rejection, entity reads, search, and recent changes is implemented.
- React dashboard for overview, ingestion, review diffs, approval/rejection, entity browsing, search, recent changes, and agent pages is implemented.
- Content Agent and GTM Agent backend endpoints are implemented with approved-main-only graph reads.
- Runtime role enforcement for reviewer, content-agent, gtm-agent, dashboard-reader, and ingestion-service is implemented.
- A Gemini structured-output LLM extraction adapter is available through environment configuration.
- A thin local MCP-style stdio wrapper is implemented under `mcp/`.
- SQLite stores workflow metadata only; approved knowledge remains in Omnigraph.
- Verified on Windows with `python -m pytest -q --basetemp .tmp\pytest-agents`: 48 tests passed.
- Verified API smoke checks: `GET /health` and `GET /openapi.json`.
- Deployment files and a governed five-document workflow helper are prepared but not deployed.
- Real local `main` has been populated through governed HITL approval for the five seed documents.
- Native Omnigraph policy is configured for coarse graph actions; node-type restrictions are enforced in API/MCP code.

Limitations:

- LLM extraction requires `EXTRACTION_PROVIDER=llm`, `LLM_PROVIDER=gemini`, `LLM_MODEL`, and `LLM_API_KEY`.
- Agent responses are deterministic by default; LLM rewriting is intentionally optional.
- The MCP wrapper is local stdio-focused. Hosted HTTP/SSE MCP is deployment preparation only.
- No final hosted deployment or Git push has been performed.
- The current verified implementation is on `codex-analysis` with uncommitted local changes; it has not been committed to `main`.

Run tests:

```powershell
python -m pytest -q --basetemp .tmp\pytest-api
```

Run the full current test suite:

```powershell
python -m pytest -q --basetemp .tmp\pytest-agents
```

Start the API:

```powershell
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

Verify API health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Verify OpenAPI:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/openapi.json
```

Run the agents:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/agents/content -ContentType "application/json" -Body '{"topic":"reducing manufacturing inventory","actor":"content-agent"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/agents/gtm -ContentType "application/json" -Body '{"product":"Stockly","actor":"gtm-agent"}'
```

Run local MCP wrapper:

```powershell
python -m mcp.server
```

Run five-document governed helper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\five_document_flow.ps1
```

Install and build the dashboard:

```powershell
Set-Location apps\dashboard
npm install
npm run build
```

Run the dashboard locally:

```powershell
Set-Location apps\dashboard
npm run dev -- --host 127.0.0.1
```

Lint Omnigraph queries:

```powershell
Get-ChildItem omnigraph\queries\*.gq | ForEach-Object {
    & "$HOME\.local\bin\omnigraph.exe" lint --schema omnigraph\schema.pg --query $_.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Lint failed for $($_.FullName)"
    }
}
```
