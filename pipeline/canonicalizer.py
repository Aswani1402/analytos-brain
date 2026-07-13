from __future__ import annotations

from .models import ExtractionPayload


def dedupe_payload(payload: ExtractionPayload) -> ExtractionPayload:
    nodes = {}
    for node in payload.nodes:
        nodes[(node.node_type, node.slug)] = node

    edges = {}
    for edge in payload.edges:
        edges[(edge.edge, edge.from_slug, edge.to_slug)] = edge

    return ExtractionPayload(nodes=list(nodes.values()), edges=list(edges.values()))
