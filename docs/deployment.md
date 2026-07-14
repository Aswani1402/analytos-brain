# Deployment

Deployed on Railway:

- Backend URL: https://analytos-brain-api-production.up.railway.app
- Hosted MCP URL: https://analytos-brain-api-production.up.railway.app/mcp
- Dashboard URL: https://analytos-brain-dashboard-production.up.railway.app
- Project: `analytos-brain`
- Backend service: `analytos-brain-api`
- Dashboard service: `analytos-brain-dashboard`
- Backend persistent volume: `/var/lib/omnigraph`

Deployment artifacts:

- `Dockerfile.api` for FastAPI.
- `Dockerfile.api` installs pinned Omnigraph v0.8.1 release binaries for both
  `omnigraph` and `omnigraph-server`.
- `apps/dashboard/Dockerfile` for the React dashboard.
- `docker-compose.yml` for local API/dashboard/storage wiring.
- `railway.toml` for the backend service.
- `scripts/start-hosted.sh` for Railway-style startup.
- `.github/workflows/backend-container.yml` for container build/smoke validation
  after push.

Environment variables:

- `OMNIGRAPH_BIN`
- `OMNIGRAPH_SERVER_BIN`
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
- `OMNIGRAPH_CLUSTER`
- `OMNIGRAPH_TEMPLATE`
- `OMNIGRAPH_SERVER_BIND`
- `ANALYTOS_START_OMNIGRAPH_SERVER`
- `OMNIGRAPH_SERVER_BEARER_TOKENS_JSON`
- `ANALYTOS_MCP_TOKENS_JSON`
- `ANALYTOS_API_TOKEN`

Simplest viable hosting:

1. FastAPI on Railway, Render, Fly.io, or a small VPS.
2. Dashboard as a static build pointed at the API origin.
3. Mounted graph storage controlled by the backend. The current FastAPI app
   uses the local Omnigraph CLI/store path, so `omnigraph-server` is installed
   and verified but not launched by default.
4. MCP wrapper as stdio locally; for hosted MCP, wrap `mcp.server.call_tool`
   behind a small FastAPI HTTP/SSE service using the same role rules.
5. S3-compatible storage or local RustFS for graph/object state where needed.

Practical local deployment check:

```powershell
docker compose build
docker compose up api dashboard
```

## Railway Backend Service

1. Create a Railway service from the GitHub repository.
2. Select `Dockerfile.api`.
3. Attach a persistent volume at `/var/lib/omnigraph`.
4. Configure variables:

```text
ANALYTOS_DB_PATH=/var/lib/omnigraph/app/analytos_brain.db
INGEST_OUTPUT_DIR=/var/lib/omnigraph/app/ingestion
OMNIGRAPH_CLUSTER=/var/lib/omnigraph/cluster
OMNIGRAPH_GRAPH_URI=/var/lib/omnigraph/cluster/graphs/knowledge.omni
OMNIGRAPH_BIN=/usr/local/bin/omnigraph
OMNIGRAPH_SERVER_BIN=/usr/local/bin/omnigraph-server
OMNIGRAPH_TEMPLATE=/app/omnigraph
ANALYTOS_START_OMNIGRAPH_SERVER=0
OMNIGRAPH_ACTOR=ingestion-service
ANALYTOS_MCP_TOKENS_JSON=<secret JSON mapping token to actor>
ANALYTOS_API_TOKEN=<secret>
ANALYTOS_CORS_ORIGINS=<dashboard URL>
EXTRACTION_PROVIDER=rule-based
PROMPT_VERSION=v1
```

Optional LLM variables:

```text
LLM_PROVIDER=gemini
LLM_MODEL=<Gemini Flash model>
LLM_API_KEY=<secret>
```

The backend exposes FastAPI and hosted MCP at the same public origin:

- `/health`
- `/mcp`
- `/ingestions`
- `/reviews`
- `/agents/content`
- `/agents/gtm`

`scripts/start-hosted.sh` copies the committed cluster template into the
persistent volume only when `cluster.yaml` is missing. It verifies both
Omnigraph executables, prints their versions, creates persistent directories,
initializes the local graph only when the graph file is absent, then runs
cluster validate, plan, and apply before starting FastAPI on Railway `$PORT`.
It does not overwrite an existing persistent cluster/runtime or graph.

Important: `Dockerfile.api` downloads the official
`ModernRelay/omnigraph` v0.8.1 Linux release asset for the build architecture,
checks the published `.sha256` file, installs `omnigraph` into
`/usr/local/bin`, installs the upstream server binary as
`/usr/local/bin/omnigraph-server.bin`, and installs a small
`/usr/local/bin/omnigraph-server` wrapper that supports `--version` before
delegating normal server arguments to the upstream binary. The build marks them
executable and runs:

```text
omnigraph version
omnigraph-server --version
```

Linux amd64 and arm64 are handled explicitly. Unsupported architectures fail at
build time instead of installing the wrong binary. Do not commit local graph
files, SQLite files, or secrets.

Verify hosted health:

```powershell
Invoke-RestMethod https://analytos-brain-api-production.up.railway.app/health
Invoke-RestMethod https://analytos-brain-api-production.up.railway.app/mcp
```

Inspect Railway build logs for:

- the Omnigraph v0.8.1 release asset download
- checksum verification
- `omnigraph version`
- `omnigraph-server --version`
- cluster validate, plan, and apply during startup

## Railway Dashboard Service

1. Create a second Railway service named `analytos-brain-dashboard`.
2. Set `VITE_API_BASE_URL` to the backend public URL.
3. Deploy the `apps/dashboard` directory as the service root with
   `./Dockerfile`.
4. Generate the dashboard domain.
5. Update backend `ANALYTOS_CORS_ORIGINS` to the exact dashboard URL.

No browser-visible secret should be added to the frontend bundle.

Note: the repository-level `railway.toml` is intentionally backend-oriented, so
GitHub-triggered Railway deployments use `Dockerfile.api`. The dashboard was
deployed to its Railway service from an `apps/dashboard` archive with
`RAILWAY_DOCKERFILE_PATH=./Dockerfile`.

## Hosted Bootstrap

The hosted graph was populated only through governed API/HITL:

```powershell
python scripts\hosted_bootstrap.py --base-url https://analytos-brain-api-production.up.railway.app --api-token <secret> --reviewer reviewer-demo
python scripts\mcp_http_smoke.py --base-url https://analytos-brain-api-production.up.railway.app --token <content-agent-mcp-token>
```

The hosted verification ingested all five seed documents, inspected review
diffs, approved through HITL as `reviewer-demo`, reran the Stockly product
document for idempotency, verified agents/MCP/access control, and never loaded
directly into `main`. Sanitized results are in
`docs/demo-output/hosted/hosted-verification.json`.

Before real hosting:

- push the repo so GitHub Actions can run the backend container smoke check
- set `VITE_API_BASE_URL` during dashboard build
- configure persistent graph storage
- pass `LLM_API_KEY` only as a secret environment variable
- run `python scripts\hosted_bootstrap.py` only after the backend is healthy
- rerun `python -m pytest -q --basetemp .tmp\pytest-final`

Docker is not installed in this local Windows environment, so this repository
does not claim a local image build. The first real container build should occur
in GitHub Actions or Railway.
