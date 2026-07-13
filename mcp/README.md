# Analytos Brain MCP

This project ships a thin local MCP-style stdio wrapper in `mcp/server.py`.
It was chosen because the assignment requires the same application-level
role filtering used by FastAPI agents. The wrapper exposes only approved
`main` graph data to agent roles and uses the shared access-control module.

Start locally:

```powershell
python -m mcp.server
```

One-shot smoke call:

```powershell
python -m mcp.server --tool search_context --actor content-agent --query Stockly
```
