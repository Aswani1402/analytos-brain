# Submission Checklist

## Links

- GitHub repository URL: https://github.com/Aswani1402/analytos-brain
- Hosted dashboard URL: https://analytos-brain-dashboard-production.up.railway.app
- Hosted MCP URL: https://analytos-brain-api-production.up.railway.app/mcp
- Backend URL: https://analytos-brain-api-production.up.railway.app
- Credentials: Railway/API/MCP secrets are stored outside the repository and must not be pasted into this checklist.
- Demo video URL: `[paste demo video URL]`
- Resume Drive URL: `[paste resume Drive URL]`

## Email

- Recipient emails: `[paste required recipient emails]`
- Subject line: `Analytos Brain Assignment Submission - Aswini Ayappan`

## Five-Minute Demo Sequence

1. Open README and explain the governed architecture.
2. Show `/health` and dashboard overview.
3. Show five seed documents were ingested through review branches.
4. Show review diff and reviewer attribution with `reviewer-demo`.
5. Show approved `main` graph snapshot counts.
6. Run Content Agent and show three approved facts, graph slugs, and sources.
7. Run GTM Agent and show ICP, persona, proof points, and illustrative companies.
8. Run MCP `search_context` and a denied internal email search.
9. Show access-control tests and native policy validation.
10. Show deployment docs and state what remains before hosted production.

## Known Limitation Disclosure

Omnigraph 0.8.1 native policy is configured and validates for coarse graph and
branch actions. Fine-grained node-type restrictions such as denied EmailThread
reads are enforced by `apps/api/access_control.py` and MCP record filtering.

Hosted deployment has been performed on Railway. The backend container installed
and verified Omnigraph v0.8.1 in Railway, checksum verification passed, the
persistent volume is mounted at `/var/lib/omnigraph`, and the governed
five-document HITL flow populated hosted `main`. Sanitized hosted verification
output is in `docs/demo-output/hosted/hosted-verification.json`.

## Railway Variables Checklist

- `ANALYTOS_DB_PATH`
- `INGEST_OUTPUT_DIR`
- `OMNIGRAPH_CLUSTER`
- `OMNIGRAPH_GRAPH_URI`
- `OMNIGRAPH_BIN`
- `OMNIGRAPH_SERVER_BIN`
- `OMNIGRAPH_TEMPLATE`
- `ANALYTOS_START_OMNIGRAPH_SERVER`
- `ANALYTOS_API_TOKEN`
- `ANALYTOS_MCP_TOKENS_JSON`
- `ANALYTOS_CORS_ORIGINS`
- `VITE_API_BASE_URL`
