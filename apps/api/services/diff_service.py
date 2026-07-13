from __future__ import annotations

from collections import Counter
from typing import Any

from .omnigraph_service import OmnigraphService


def _clean_data(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in sorted(data.items()) if key != "id"}


def _node_key(record: dict[str, Any]) -> tuple[str, str]:
    data = record.get("data") or {}
    return record["type"], data["slug"]


def _edge_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return record["edge"], record["from"], record["to"]


def _sort_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda record: (record.get("type") or record.get("edge") or "", record.get("from") or "", record.get("to") or "", (record.get("data") or {}).get("slug", "")))


class DiffService:
    def __init__(self, omnigraph: OmnigraphService):
        self.omnigraph = omnigraph

    def diff(self, branch_name: str, base_branch: str = "main") -> dict[str, Any]:
        base_records = self.omnigraph.export_branch(base_branch)
        branch_records = self.omnigraph.export_branch(branch_name)
        return self.diff_records(base_records, branch_records)

    def diff_records(self, base_records: list[dict[str, Any]], branch_records: list[dict[str, Any]]) -> dict[str, Any]:
        base_nodes = {_node_key(record): record for record in base_records if "type" in record}
        branch_nodes = {_node_key(record): record for record in branch_records if "type" in record}
        base_edges = {_edge_key(record): record for record in base_records if "edge" in record}
        branch_edges = {_edge_key(record): record for record in branch_records if "edge" in record}

        added_nodes = [branch_nodes[key] for key in branch_nodes.keys() - base_nodes.keys()]
        removed_nodes = [base_nodes[key] for key in base_nodes.keys() - branch_nodes.keys()]
        changed_nodes = [
            {"before": base_nodes[key], "after": branch_nodes[key]}
            for key in branch_nodes.keys() & base_nodes.keys()
            if _clean_data(base_nodes[key].get("data") or {}) != _clean_data(branch_nodes[key].get("data") or {})
        ]

        added_edges = [branch_edges[key] for key in branch_edges.keys() - base_edges.keys()]
        removed_edges = [base_edges[key] for key in base_edges.keys() - branch_edges.keys()]
        changed_edges = [
            {"before": base_edges[key], "after": branch_edges[key]}
            for key in branch_edges.keys() & base_edges.keys()
            if _clean_data(base_edges[key].get("data") or {}) != _clean_data(branch_edges[key].get("data") or {})
        ]

        node_counts = Counter(record["type"] for record in added_nodes)
        edge_counts = Counter(record["edge"] for record in added_edges)
        confidence_values = sorted(
            {
                str((record.get("data") or {}).get("confidence"))
                for record in added_nodes + added_edges
                if (record.get("data") or {}).get("confidence") is not None
            }
        )
        provenance = [
            {
                "type": record.get("type") or record.get("edge"),
                "slug": (record.get("data") or {}).get("slug"),
                "from": record.get("from"),
                "to": record.get("to"),
                "source_document_id": (record.get("data") or {}).get("source_document_id"),
                "source_file": (record.get("data") or {}).get("source_file"),
                "source_excerpt": (record.get("data") or {}).get("source_excerpt"),
            }
            for record in _sort_records(added_nodes + added_edges)
        ]
        visibility = Counter(str((record.get("data") or {}).get("visibility", "unspecified")) for record in added_nodes)

        return {
            "added_nodes": _sort_records(added_nodes),
            "changed_nodes": sorted(changed_nodes, key=lambda item: _node_key(item["after"])),
            "removed_nodes": _sort_records(removed_nodes),
            "added_edges": _sort_records(added_edges),
            "changed_edges": sorted(changed_edges, key=lambda item: _edge_key(item["after"])),
            "removed_edges": _sort_records(removed_edges),
            "counts": {
                "nodes": len(added_nodes),
                "edges": len(added_edges),
                "by_node_type": dict(sorted(node_counts.items())),
                "by_edge_type": dict(sorted(edge_counts.items())),
            },
            "confidence": confidence_values,
            "provenance": provenance,
            "visibility": dict(sorted(visibility.items())),
        }

    def business_edge_keys(self, records: list[dict[str, Any]]) -> set[tuple[str, str, str]]:
        return {_edge_key(record) for record in records if "edge" in record}
