from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.dependencies import get_omnigraph_service
from apps.api.routers import mcp_http


def _record(node_type: str, slug: str, **data):
    payload = {
        "slug": slug,
        "name": data.pop("name", slug),
        "visibility": data.pop("visibility", "internal"),
        "source_file": data.pop("source_file", "seed-data/test.md"),
        "source_excerpt": data.pop("source_excerpt", slug),
        **data,
    }
    return {"type": node_type, "data": payload}


class FakeOmnigraph:
    def export_branch(self, branch_name, type_name=None):
        assert branch_name == "main"
        records = [
            _record("Product", "product:stockly", name="Stockly", summary="Inventory intelligence"),
            _record("Feature", "feature:stockly:pull-kanban", name="Pull Kanban", description="Kanban sizing"),
            _record(
                "ProofPoint",
                "proof:stockly:21-percent",
                name="21 percent inventory reduction",
                proof_type="metric",
                metric_name="inventory",
                metric_value="21%",
                result="21% reduction",
                approved_for_external_use="true",
                visibility="external_approved",
            ),
            _record("EmailThread", "email-thread:secret", subject="Secret Stockly pilot", visibility="internal"),
            _record("ICPSegment", "icp:mid-market", name="Mid-market", segment_type="direct", trigger_signals="kanban on cards"),
            _record("Persona", "persona:plant-manager", name="Plant Manager", cares_about="stockouts"),
        ]
        if type_name:
            return [record for record in records if record["type"] == type_name]
        return records

    def list_commits(self, branch="main"):
        return [{"branch": branch, "actor": "reviewer-demo"}]


def client(monkeypatch):
    monkeypatch.setenv("ANALYTOS_MCP_TOKENS_JSON", '{"content-token":"content-agent","gtm-token":"gtm-agent"}')
    app = FastAPI()
    app.include_router(mcp_http.router)
    app.dependency_overrides[get_omnigraph_service] = lambda: FakeOmnigraph()
    return TestClient(app)


def rpc(body: dict, token: str = "content-token"):
    return {"headers": {"Authorization": f"Bearer {token}"}, "json": body}


def test_mcp_initialize_and_list_tools(monkeypatch):
    c = client(monkeypatch)
    response = c.post("/mcp", **rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize"}))
    assert response.status_code == 200
    assert response.json()["result"]["serverInfo"]["name"] == "analytos-brain"
    response = c.post("/mcp", **rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
    assert response.status_code == 200
    assert "search_context" in {tool["name"] for tool in response.json()["result"]["tools"]}


def test_hosted_search_context_uses_token_actor_and_main_only(monkeypatch):
    c = client(monkeypatch)
    response = c.post(
        "/mcp",
        **rpc(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "search_context", "arguments": {"query": "Stockly", "actor": "gtm-agent", "branch": "pending"}},
            }
        ),
    )
    assert response.status_code == 200
    text = response.json()["result"]["content"][0]["text"]
    assert "product:stockly" in text
    assert "email-thread:secret" not in text


def test_invalid_mcp_token_is_denied(monkeypatch):
    c = client(monkeypatch)
    response = c.post("/mcp", **rpc({"jsonrpc": "2.0", "id": 4, "method": "tools/list"}, token="bad"))
    assert response.status_code == 401


def test_gtm_agent_can_access_icp(monkeypatch):
    c = client(monkeypatch)
    response = c.post(
        "/mcp",
        **rpc({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "get_icp_segments", "arguments": {}}}, token="gtm-token"),
    )
    assert response.status_code == 200
    assert "icp:mid-market" in response.json()["result"]["content"][0]["text"]
