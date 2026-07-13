Analytos Brain
==============

Current completion status:

- Typed Omnigraph schema and stored read queries are implemented.
- Rule-based seed extraction and branch-isolated ingestion are implemented.
- FastAPI backend for ingestion, HITL review, approval, rejection, entity reads, search, and recent changes is implemented.
- SQLite stores workflow metadata only; approved knowledge remains in Omnigraph.
- Verified on Windows with `python -m pytest -q --basetemp .tmp\pytest-api`: 38 tests passed twice.
- Verified API smoke checks: `GET /health` and `GET /openapi.json`.
- React dashboard, production agents, MCP integration, Cedar policies, deployment, and demo workflow are not built yet.

Run tests:

```powershell
python -m pytest -q --basetemp .tmp\pytest-api
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

Lint Omnigraph queries:

```powershell
Get-ChildItem omnigraph\queries\*.gq | ForEach-Object {
    & "$HOME\.local\bin\omnigraph.exe" lint --schema omnigraph\schema.pg --query $_.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Lint failed for $($_.FullName)"
    }
}
```
