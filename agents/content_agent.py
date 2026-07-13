from __future__ import annotations

from typing import Any

from apps.api.access_control import require_allowed

from .common import InsufficientEvidenceError, facts_from_records, main_records, scrub_confidential, unique_sources


def run_content_agent(omnigraph, topic: str, actor: str = "content-agent", use_llm: bool = False) -> dict[str, Any]:
    require_allowed(actor, "run_content_agent", branch="main")
    records = main_records(omnigraph, actor)
    proof_facts = facts_from_records(records, proof_only=True)
    if len(proof_facts) < 3:
        raise InsufficientEvidenceError("Content Agent needs at least three externally approved proof points in main.")
    selected = proof_facts[:3]
    title = f"How AI Helps Manufacturers With {topic.title()}"
    bullets = "\n".join(f"- {fact.name}: {scrub_confidential(fact.fact)}" for fact in selected)
    draft = (
        f"# {title}\n\n"
        f"Manufacturers working on {topic} need practical evidence, not vague automation claims. "
        "Analytos approved graph evidence points to measurable operational gains when teams keep a human review loop around AI recommendations.\n\n"
        f"{bullets}\n\n"
        "These proof points support a focused story: start with constrained workflows, keep source provenance visible, and use approved metrics only when speaking externally."
    )
    return {
        "title": title,
        "blog_draft": draft,
        "draft": draft,
        "facts_used": [{"slug": fact.slug, "name": fact.name, "fact": scrub_confidential(fact.fact)} for fact in selected],
        "graph_node_slugs": [fact.slug for fact in selected],
        "source_documents": unique_sources(selected),
        "graph_evidence": [fact.record for fact in selected],
        "generation_mode": "llm" if use_llm else "deterministic",
    }
