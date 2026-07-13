from __future__ import annotations

from typing import Any

from apps.api.access_control import require_allowed

from .common import InsufficientEvidenceError, facts_from_records, main_records, unique_sources


def run_gtm_agent(omnigraph, product: str, actor: str = "gtm-agent", use_llm: bool = False) -> dict[str, Any]:
    require_allowed(actor, "run_gtm_agent", branch="main")
    records = main_records(omnigraph, actor)
    product_slug = f"product:{product.lower().strip().replace(' ', '-')}"
    product_records = [record for record in records if record.get("type") == "Product" and (record.get("data") or {}).get("slug") == product_slug]
    icp_records = [record for record in records if record.get("type") == "ICPSegment"]
    persona_records = [record for record in records if record.get("type") == "Persona"]
    proof_facts = facts_from_records(records, proof_only=True)
    if not product_records or not icp_records or not persona_records or len(proof_facts) < 1:
        raise InsufficientEvidenceError("GTM Agent needs an approved product, ICP/persona context, and at least one externally approved proof point in main.")

    product_data = product_records[0]["data"]
    icp = icp_records[0]["data"]
    persona = persona_records[0]["data"]
    selected_proofs = proof_facts[:3]
    source_facts = selected_proofs + facts_from_records([product_records[0], icp_records[0], persona_records[0]])
    return {
        "target_company_profile": {
            "product": product_data.get("name"),
            "firmographics": {
                "revenue_range": icp.get("revenue_range"),
                "employee_range": icp.get("employee_range"),
                "plant_range": icp.get("plant_range"),
            },
            "industries": icp.get("sectors"),
            "company_size": icp.get("employee_range"),
            "geography": icp.get("geography"),
            "erp_or_technical_signals": icp.get("erp_footprint"),
            "trigger_signals": icp.get("trigger_signals"),
        },
        "persona_to_contact": {
            "name": persona.get("name"),
            "role_in_deal": persona.get("role_in_deal"),
            "pains_and_goals": persona.get("cares_about"),
            "winning_message": persona.get("winning_message"),
        },
        "competitor_or_displacement_angle": product_data.get("competitive_alternatives") or "Position against spreadsheet-heavy manual workflows and forecast-push planning when supported by approved graph evidence.",
        "illustrative_companies": [
            {"name": "Midwest Precision Components", "label": "illustrative/plausible example, not a graph fact"},
            {"name": "Southeast Medical Assemblies", "label": "illustrative/plausible example, not a graph fact"},
            {"name": "Great Lakes Industrial Equipment", "label": "illustrative/plausible example, not a graph fact"},
        ],
        "grounded_opening_angle": f"Lead with {selected_proofs[0].name}: {selected_proofs[0].fact}",
        "approved_proof_points_used": [{"slug": fact.slug, "name": fact.name, "fact": fact.fact} for fact in selected_proofs],
        "graph_node_slugs": [fact.slug for fact in source_facts],
        "source_documents": unique_sources(source_facts),
        "graph_evidence": [fact.record for fact in source_facts],
        "generation_mode": "llm" if use_llm else "deterministic",
    }
