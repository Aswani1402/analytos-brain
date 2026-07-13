from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Visibility = Literal["internal", "external_approved", "restricted"]


class Provenance(BaseModel):
    source_document_id: str | None = None
    source_file: str | None = None
    source_excerpt: str | None = None
    confidence: str | None = None
    visibility: Visibility = "internal"
    created_at: str | None = None
    updated_at: str | None = None


class NodeBase(Provenance):
    model_config = ConfigDict(extra="forbid")

    node_type: ClassVar[str]
    slug: str

    @field_validator("slug")
    @classmethod
    def slug_must_be_deterministic(cls, value: str) -> str:
        if ":" not in value:
            raise ValueError("slug must include a type prefix")
        return value

    def to_omnigraph(self) -> dict[str, Any]:
        data = self.model_dump(exclude_none=True)
        data["id"] = self.slug
        return {"type": self.node_type, "data": data}


class Product(NodeBase):
    node_type: ClassVar[str] = "Product"
    name: str
    site_url: str | None = None
    category: str | None = None
    owner: str | None = None
    status: str
    summary: str | None = None
    positioning: str | None = None
    competitive_alternatives: str | None = None
    technical_stack: str | None = None
    target_buyer: str | None = None


class Feature(NodeBase):
    node_type: ClassVar[str] = "Feature"
    name: str
    product_area: str | None = None
    description: str | None = None
    feature_type: str | None = None
    status: str | None = None
    autonomy_level: str | None = None
    integration_system: str | None = None


class ProofPoint(NodeBase):
    node_type: ClassVar[str] = "ProofPoint"
    name: str
    proof_type: str
    metric_name: str | None = None
    metric_value: str | None = None
    baseline: str | None = None
    result: str | None = None
    timeframe: str | None = None
    customer_segment: str | None = None
    approved_for_external_use: Literal["true", "false"] = "false"
    external_label: str | None = None
    confidentiality_note: str | None = None


class Persona(NodeBase):
    node_type: ClassVar[str] = "Persona"
    name: str
    role_in_deal: str | None = None
    product_focus: str | None = None
    cares_about: str | None = None
    losing_message: str | None = None
    winning_message: str | None = None
    economic_role: str | None = None


class ICPSegment(NodeBase):
    node_type: ClassVar[str] = "ICPSegment"
    name: str
    segment_type: str
    revenue_range: str | None = None
    employee_range: str | None = None
    plant_range: str | None = None
    sectors: str | None = None
    erp_footprint: str | None = None
    geography: str | None = None
    trigger_signals: str | None = None
    disqualifiers: str | None = None
    channel_notes: str | None = None
    value_framing: str | None = None
    status: str | None = None


class Person(NodeBase):
    node_type: ClassVar[str] = "Person"
    name: str
    email: str | None = None
    organization: str | None = None
    role: str | None = None
    person_type: str


class EmailThread(NodeBase):
    node_type: ClassVar[str] = "EmailThread"
    subject: str
    thread_date: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    participants: str | None = None
    summary: str | None = None
    status: str = "pending_review"
    sensitivity: str = "internal"


class Decision(NodeBase):
    node_type: ClassVar[str] = "Decision"
    title: str
    decision_type: str
    status: str
    summary: str | None = None
    decision_date: str | None = None
    external_approval_status: str | None = None
    confidentiality_note: str | None = None


class SourceDocument(NodeBase):
    node_type: ClassVar[str] = "SourceDocument"
    file_name: str
    document_type: str
    title: str | None = None
    content_hash: str
    reviewed_at: str | None = None


class ExtractionRun(NodeBase):
    node_type: ClassVar[str] = "ExtractionRun"
    branch_name: str
    model_name: str
    prompt_version: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    source_count: str | None = None
    notes: str | None = None


GraphNode = Product | Feature | ProofPoint | Persona | ICPSegment | Person | EmailThread | Decision | SourceDocument | ExtractionRun


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edge: Literal[
        "HasFeature",
        "ProvenBy",
        "SupportedBy",
        "Targets",
        "HasPersona",
        "Discusses",
        "DiscussedIn",
        "DecidedBy",
        "Processed",
    ]
    from_slug: str = Field(alias="from")
    to_slug: str = Field(alias="to")
    source_document_id: str | None = None
    source_file: str | None = None
    source_excerpt: str | None = None
    confidence: str | None = None
    created_at: str | None = None

    def to_omnigraph(self) -> dict[str, Any]:
        data = self.model_dump(exclude_none=True, by_alias=True)
        return {
            "edge": self.edge,
            "from": data.pop("from"),
            "to": data.pop("to"),
            "data": data,
        }


class ExtractionPayload(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]

    def review_summary(self) -> dict[str, int]:
        node_counts: dict[str, int] = {}
        edge_counts: dict[str, int] = {}
        for node in self.nodes:
            node_counts[node.node_type] = node_counts.get(node.node_type, 0) + 1
        for edge in self.edges:
            edge_counts[edge.edge] = edge_counts.get(edge.edge, 0) + 1
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            **{f"node:{key}": value for key, value in sorted(node_counts.items())},
            **{f"edge:{key}": value for key, value in sorted(edge_counts.items())},
        }
