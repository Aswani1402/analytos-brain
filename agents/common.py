from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.api.access_control import is_allowed_node, require_allowed


class InsufficientEvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class GraphFact:
    slug: str
    node_type: str
    name: str
    fact: str
    source_document: str | None
    source_excerpt: str | None
    record: dict[str, Any]


def main_records(omnigraph, actor: str) -> list[dict[str, Any]]:
    require_allowed(actor, "read_main", branch="main")
    return [record for record in omnigraph.export_branch("main") if "type" in record and is_allowed_node(actor, record, branch="main")]


def facts_from_records(records: list[dict[str, Any]], *, proof_only: bool = False) -> list[GraphFact]:
    facts: list[GraphFact] = []
    for record in records:
        data = record.get("data") or {}
        node_type = record.get("type")
        if proof_only and node_type != "ProofPoint":
            continue
        if node_type == "ProofPoint" and not (data.get("approved_for_external_use") == "true" and data.get("visibility") == "external_approved"):
            continue
        text = _fact_text(node_type, data)
        if text:
            facts.append(
                GraphFact(
                    slug=str(data.get("slug")),
                    node_type=str(node_type),
                    name=str(data.get("name") or data.get("title") or data.get("slug")),
                    fact=text,
                    source_document=data.get("source_file"),
                    source_excerpt=data.get("source_excerpt"),
                    record=record,
                )
            )
    return facts


def _fact_text(node_type: str | None, data: dict[str, Any]) -> str:
    if node_type == "ProofPoint":
        metric = " ".join(str(data.get(key)) for key in ("metric_name", "metric_value", "result") if data.get(key))
        return metric.strip()
    if node_type == "Feature":
        return str(data.get("description") or "")
    if node_type == "Product":
        return str(data.get("summary") or data.get("category") or "")
    if node_type == "ICPSegment":
        return str(data.get("trigger_signals") or data.get("sectors") or "")
    if node_type == "Persona":
        return str(data.get("cares_about") or data.get("winning_message") or "")
    return ""


def unique_sources(facts: list[GraphFact]) -> list[str]:
    return sorted({fact.source_document for fact in facts if fact.source_document})


def scrub_confidential(text: str) -> str:
    blocked = ["confidential client", "Client name", "client name must remain confidential"]
    scrubbed = text
    for phrase in blocked:
        scrubbed = scrubbed.replace(phrase, "approved anonymous customer")
    return scrubbed
