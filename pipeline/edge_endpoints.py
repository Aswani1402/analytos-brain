from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .id_generator import slugify
from .models import ExtractionPayload, Feature, GraphNode, Product


EDGE_ENDPOINT_TYPES: dict[str, tuple[str, str]] = {
    "HasFeature": ("Product", "Feature"),
    "ProvenBy": ("Product", "ProofPoint"),
    "SupportedBy": ("Feature", "ProofPoint"),
    "Targets": ("Product", "ICPSegment"),
    "HasPersona": ("ICPSegment", "Persona"),
    "Discusses": ("EmailThread", "Product"),
    "DiscussedIn": ("Decision", "EmailThread"),
    "DecidedBy": ("Decision", "Person"),
    "Processed": ("ExtractionRun", "SourceDocument"),
}


class UnsatisfiedEdgeEndpointError(ValueError):
    pass


def canonical_product_reference(name: str) -> Product:
    slug = slugify(name)
    if slug == "stockly":
        return Product(
            slug="product:stockly",
            name="Stockly",
            site_url="stockly.analytos.ai",
            category="Pull Kanban inventory intelligence for discrete manufacturing",
            owner="Analytos Labs product team",
            status="in_production_pilot_customers",
            summary="AI-driven Pull Kanban engine that right-sizes kanban loops and safety stock.",
            source_file="seed-data/stockly-product-overview.md",
            source_excerpt="Stockly product overview canonical reference",
            confidence="0.90",
            visibility="internal",
        )
    if slug == "inspectly":
        return Product(
            slug="product:inspectly",
            name="Inspectly",
            site_url="inspectly.analytos.ai",
            category="Engineering drawing to inspection plan automation",
            owner="Analytos Labs product team",
            status="in_production_customer",
            summary="Reads engineering drawings and generates ballooned inspection plan workbooks.",
            source_file="seed-data/inspectly-product-overview.md",
            source_excerpt="Inspectly product overview canonical reference",
            confidence="0.90",
            visibility="internal",
        )
    raise KeyError(f"No canonical Product reference for {name!r}")


def canonical_feature_reference(product: str, name: str) -> Feature:
    product_slug = slugify(product)
    feature_slug = slugify(name)
    if product_slug == "stockly" and feature_slug == "supplier-lead-time-intelligence":
        return Feature(
            slug="feature:stockly:supplier-lead-time-intelligence",
            name="Supplier lead-time intelligence",
            product_area="Stockly",
            description="Learns actual versus quoted supplier lead times.",
            feature_type="capability",
            status="active",
            source_file="seed-data/stockly-product-overview.md",
            source_excerpt="Supplier lead-time intelligence",
            confidence="0.90",
            visibility="internal",
        )
    if product_slug == "inspectly" and feature_slug == "revision-diffing":
        return Feature(
            slug="feature:inspectly:revision-diffing",
            name="Revision diffing",
            product_area="Inspectly",
            description="Highlights changed characteristics between revisions.",
            feature_type="capability",
            status="active",
            source_file="seed-data/inspectly-product-overview.md",
            source_excerpt="Revision diffing",
            confidence="0.90",
            visibility="internal",
        )
    raise KeyError(f"No canonical Feature reference for {product!r} / {name!r}")


def canonical_reference_for(slug: str, node_type: str) -> GraphNode | None:
    if node_type == "Product" and slug == "product:stockly":
        return canonical_product_reference("Stockly")
    if node_type == "Product" and slug == "product:inspectly":
        return canonical_product_reference("Inspectly")
    if node_type == "Feature" and slug == "feature:stockly:supplier-lead-time-intelligence":
        return canonical_feature_reference("Stockly", "Supplier lead-time intelligence")
    if node_type == "Feature" and slug == "feature:inspectly:revision-diffing":
        return canonical_feature_reference("Inspectly", "Revision diffing")
    return None


def ensure_edge_endpoints(
    payload: ExtractionPayload,
    existing_nodes: Mapping[str, GraphNode] | None = None,
) -> ExtractionPayload:
    nodes_by_slug = {node.slug: node for node in payload.nodes}
    existing_nodes = existing_nodes or {}
    added_nodes: list[GraphNode] = []

    for edge in payload.edges:
        try:
            from_type, to_type = EDGE_ENDPOINT_TYPES[edge.edge]
        except KeyError as exc:
            raise UnsatisfiedEdgeEndpointError(f"Unknown edge type {edge.edge!r}") from exc
        for slug, expected_type, direction in (
            (edge.from_slug, from_type, "from"),
            (edge.to_slug, to_type, "to"),
        ):
            node = nodes_by_slug.get(slug)
            if node is None:
                node = existing_nodes.get(slug)
                if node is None:
                    node = canonical_reference_for(slug, expected_type)
                if node is not None:
                    nodes_by_slug[slug] = node
                    added_nodes.append(node)
            if node is None:
                raise UnsatisfiedEdgeEndpointError(
                    f"Unsatisfied {direction} endpoint for {edge.edge}: "
                    f"{slug!r} is not present in the payload and no safe {expected_type} reference is available"
                )
            if node.node_type != expected_type:
                raise UnsatisfiedEdgeEndpointError(
                    f"Invalid {direction} endpoint for {edge.edge}: "
                    f"{slug!r} is {node.node_type}, expected {expected_type}"
                )

    if not added_nodes:
        return payload
    return ExtractionPayload(nodes=[*payload.nodes, *added_nodes], edges=payload.edges)


def validate_edge_endpoints(payload: ExtractionPayload) -> None:
    ensure_edge_endpoints(payload, existing_nodes={})


def load_existing_nodes_from_jsonl(lines: Iterable[str]) -> dict[str, GraphNode]:
    nodes: dict[str, GraphNode] = {}
    for line in lines:
        if not line.strip():
            continue
        record = json.loads(line)
        node = _node_from_record(record)
        if node is not None:
            nodes[node.slug] = node
    return nodes


def load_existing_nodes_from_export(path: str | Path) -> dict[str, GraphNode]:
    return load_existing_nodes_from_jsonl(Path(path).read_text(encoding="utf-8").splitlines())


def _node_from_record(record: Mapping[str, Any]) -> GraphNode | None:
    data = dict(record.get("data") or {})
    data.pop("id", None)
    node_type = record.get("type")
    if node_type == "Product":
        return Product.model_validate(data)
    if node_type == "Feature":
        return Feature.model_validate(data)
    return None
