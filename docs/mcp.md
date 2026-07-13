# MCP

The repo includes a thin local MCP-style stdio wrapper at `mcp/server.py`.

Official package note: `npm view @modernrelay/omnigraph-mcp` reports version
`0.8.0`, a stdio MCP server using `OMNIGRAPH_BASE_URL`,
`OMNIGRAPH_GRAPH_ID`, optional `OMNIGRAPH_TOKEN`, and
`OMNIGRAPH_DEFAULT_BRANCH`. Its surface includes broad read tools plus mutating
tools such as `load`, `branches_create`, `branches_delete`, and
`branches_merge`. That is compatible with a served Omnigraph cluster, but this
assignment needs application-level Product/Feature/ProofPoint/ICP/Persona
filtering by role. The custom wrapper was added so MCP and FastAPI agents share
the same role checks in `apps/api/access_control.py`.

Tools:

- `search_context`
- `get_product`
- `get_product_features`
- `get_product_proof_points`
- `get_icp_segments`
- `get_personas`
- `get_recent_changes`
- reviewer placeholders: `list_pending_reviews`, `get_review_diff`

Start stdio:

```powershell
python -m mcp.server
```

One-shot smoke:

```powershell
python -m mcp.server --tool search_context --actor content-agent --query Stockly
```

Claude Desktop-style command:

```json
{
  "mcpServers": {
    "analytos-brain": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "C:\\Users\\Aswini_Ayappan\\OneDrive\\Desktop\\project\\analytos-brain"
    }
  }
}
```

Real graph smoke commands:

```powershell
python -m mcp.server --tool search_context --actor content-agent --query Stockly
python -m mcp.server --tool get_product --actor content-agent --slug product:stockly
python -m mcp.server --tool get_product_proof_points --actor content-agent
python -m mcp.server --tool get_icp_segments --actor gtm-agent
python -m mcp.server --tool get_personas --actor gtm-agent
python -m mcp.server --tool search_context --actor content-agent --query "Stockly pilot"
```

The final command returns no records because internal EmailThread context is
filtered out for `content-agent`.
