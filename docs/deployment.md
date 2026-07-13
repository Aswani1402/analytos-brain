# Deployment

Prepared but not deployed:

- `Dockerfile.api` for FastAPI.
- `apps/dashboard/Dockerfile` for the React dashboard.
- `docker-compose.yml` for local API/dashboard/storage wiring.

Environment variables:

- `OMNIGRAPH_BIN`
- `OMNIGRAPH_GRAPH_URI`
- `ANALYTOS_DB_PATH`
- `ANALYTOS_UPLOAD_DIR`
- `ANALYTOS_CORS_ORIGINS`
- `API_URL`
- `DASHBOARD_URL`
- `MCP_URL`
- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_API_KEY`
- `S3_ENDPOINT_URL`
- `S3_BUCKET`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `RUSTFS_ENDPOINT_URL`

Simplest viable hosting:

1. FastAPI on Railway, Render, Fly.io, or a small VPS.
2. Dashboard as a static build pointed at the API origin.
3. Omnigraph server or mounted graph storage controlled by the backend.
4. MCP wrapper as stdio locally; for hosted MCP, wrap `mcp.server.call_tool`
   behind a small FastAPI HTTP/SSE service using the same role rules.
5. S3-compatible storage or local RustFS for graph/object state where needed.

Practical local deployment check:

```powershell
docker compose build
docker compose up api dashboard
```

Before real hosting:

- install or mount `omnigraph.exe`/Omnigraph server support in the API runtime
- set `VITE_API_BASE_URL` during dashboard build
- configure persistent graph storage
- pass `LLM_API_KEY` only as a secret environment variable
- add a hosted HTTP/SSE wrapper if hosted MCP is required
- rerun `python -m pytest -q --basetemp .tmp\pytest-final`
