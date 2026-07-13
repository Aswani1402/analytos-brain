from __future__ import annotations

import pytest
from fastapi import HTTPException

from agents.common import InsufficientEvidenceError
from agents.content_agent import run_content_agent
from agents.gtm_agent import run_gtm_agent
from apps.api.access_control import decide, is_allowed_node, require_allowed
from mcp.server import call_tool


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
    def __init__(self, records):
        self.records = records
        self.branches = []

    def export_branch(self, branch_name, type_name=None):
        self.branches.append(branch_name)
        records = [record for record in self.records if "type" in record]
        if type_name:
            records = [record for record in records if record["type"] == type_name]
        return records

    def list_commits(self, branch="main"):
        return [{"branch": branch, "actor": "reviewer-aswini"}]


def approved_proof(slug: str, metric: str = "21%"):
    return _record(
        "ProofPoint",
        slug,
        proof_type="metric",
        metric_name="metric",
        metric_value=metric,
        result=f"{metric} approved result",
        approved_for_external_use="true",
        visibility="external_approved",
    )


def graph_records():
    return [
        _record("Product", "product:stockly", name="Stockly", summary="Inventory intelligence"),
        _record("Feature", "feature:stockly:pull-kanban", name="Pull Kanban", description="Kanban sizing"),
        approved_proof("proof:stockly:one", "21%"),
        approved_proof("proof:stockly:two", "35%"),
        approved_proof("proof:stockly:three", "under 1 hour/week"),
        _record("ProofPoint", "proof:secret", approved_for_external_use="false", visibility="internal", result="secret"),
        _record("EmailThread", "email-thread:secret", subject="Secret", visibility="internal"),
        _record("ICPSegment", "icp:mid-market", name="Mid-market", segment_type="direct", revenue_range="$50M-$500M", employee_range="100-2,000", plant_range="1-6", sectors="manufacturing", erp_footprint="NetSuite", geography="US", trigger_signals="kanban on cards"),
        _record("Persona", "persona:plant-manager", name="Plant Manager", role_in_deal="Champion", cares_about="stockouts", winning_message="fewer stockouts"),
    ]


def test_content_agent_uses_main_only_and_three_approved_facts():
    fake = FakeOmnigraph(graph_records())
    result = run_content_agent(fake, "inventory", actor="content-agent")
    assert fake.branches == ["main"]
    assert len(result["facts_used"]) == 3
    assert all("proof:stockly" in slug for slug in result["graph_node_slugs"])
    assert "email-thread:secret" not in str(result)


def test_content_agent_requires_three_approved_facts():
    fake = FakeOmnigraph(graph_records()[:3])
    with pytest.raises(InsufficientEvidenceError):
        run_content_agent(fake, "inventory", actor="content-agent")


def test_gtm_agent_reads_icp_persona_and_marks_companies_illustrative():
    result = run_gtm_agent(FakeOmnigraph(graph_records()), "Stockly", actor="gtm-agent")
    assert result["target_company_profile"]["industries"] == "manufacturing"
    assert result["persona_to_contact"]["name"] == "Plant Manager"
    assert all("illustrative" in item["label"] for item in result["illustrative_companies"])


def test_access_control_required_allow_and_deny_cases():
    assert decide("reviewer-aswini", "approve").allowed
    assert decide("content-agent", "run_content_agent").allowed
    assert not decide("dashboard-reader", "run_content_agent").allowed
    assert decide("gtm-agent", "run_gtm_agent").allowed
    assert not decide("dashboard-reader", "run_gtm_agent").allowed
    assert decide("content-agent", "read_node", node_type="Product").allowed
    assert decide("content-agent", "read_node", node_type="ProofPoint", approved_external=True).allowed
    assert not decide("content-agent", "read_node", node_type="EmailThread").allowed
    assert decide("gtm-agent", "read_node", node_type="ICPSegment").allowed
    assert not decide("gtm-agent", "read_node", node_type="EmailThread").allowed
    assert decide("ingestion-service", "create_ingestion_branch", branch="ingestion").allowed
    assert not decide("ingestion-service", "direct_main_write", branch="main").allowed
    with pytest.raises(HTTPException):
        require_allowed("dashboard-reader", "merge")
    with pytest.raises(HTTPException):
        run_content_agent(FakeOmnigraph(graph_records()), "inventory", actor="dashboard-reader")


def test_mcp_filters_email_thread_and_pending_branch_data():
    fake = FakeOmnigraph(graph_records())
    result = call_tool("search_context", {"actor": "content-agent", "query": "secret"}, fake)
    assert result["records"] == []
    result = call_tool("get_icp_segments", {"actor": "gtm-agent"}, fake)
    assert result["records"][0]["type"] == "ICPSegment"
    assert not is_allowed_node("content-agent", _record("EmailThread", "email-thread:x"))
