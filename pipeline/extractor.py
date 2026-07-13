from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .document_reader import SourceDocumentInput
from .id_generator import slugify
from .models import (
    Decision,
    EmailThread,
    ExtractionPayload,
    Feature,
    GraphEdge,
    ICPSegment,
    Person,
    Persona,
    Product,
    ProofPoint,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BaseExtractor:
    model_name = "unknown"

    def extract(self, document: SourceDocumentInput) -> ExtractionPayload:
        raise NotImplementedError


class RuleBasedExtractor(BaseExtractor):
    """Deterministic local extractor for tests and offline demos."""

    model_name = "mock-rule-based-v1"

    def extract(self, document: SourceDocumentInput) -> ExtractionPayload:
        name = document.file_name.lower()
        if "stockly-product-overview" in name:
            return self._stockly_product(document)
        if "inspectly-product-overview" in name:
            return self._inspectly_product(document)
        if "icp-analytos" in name:
            return self._icp(document)
        if "email-01-stockly" in name:
            return self._stockly_email(document)
        if "email-02-inspectly" in name:
            return self._inspectly_email(document)
        return ExtractionPayload(nodes=[], edges=[])

    def _common(self, document: SourceDocumentInput, excerpt: str, visibility: str = "internal") -> dict[str, str]:
        return {
            "source_document_id": document.slug,
            "source_file": document.file_name,
            "source_excerpt": excerpt,
            "confidence": "0.90",
            "visibility": visibility,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

    def _edge(self, edge: str, from_slug: str, to_slug: str, document: SourceDocumentInput, excerpt: str) -> GraphEdge:
        return GraphEdge.model_validate(
            {
                "edge": edge,
                "from": from_slug,
                "to": to_slug,
                "source_document_id": document.slug,
                "source_file": document.file_name,
                "source_excerpt": excerpt,
                "confidence": "0.90",
                "created_at": utc_now(),
            }
        )

    def _product(self, document: SourceDocumentInput, name: str, site: str, category: str, status: str, summary: str) -> Product:
        slug = f"product:{slugify(name)}"
        return Product(
            slug=slug,
            name=name,
            site_url=site,
            category=category,
            owner="Analytos Labs product team",
            status=status,
            summary=summary,
            **self._common(document, summary),
        )

    def _feature(self, document: SourceDocumentInput, product: str, name: str, description: str, feature_type: str = "capability") -> Feature:
        return Feature(
            slug=f"feature:{slugify(product)}:{slugify(name)}",
            name=name,
            product_area=product,
            description=description,
            feature_type=feature_type,
            status="active",
            **self._common(document, description),
        )

    def _proof(
        self,
        document: SourceDocumentInput,
        product: str,
        name: str,
        metric_name: str,
        metric_value: str,
        excerpt: str,
        approved: str = "true",
        visibility: str = "external_approved",
    ) -> ProofPoint:
        return ProofPoint(
            slug=f"proof:{slugify(product)}:{slugify(name)}",
            name=name,
            proof_type="metric",
            metric_name=metric_name,
            metric_value=metric_value,
            result=excerpt,
            approved_for_external_use=approved,
            external_label="anonymous customer",
            confidentiality_note="Client name must remain confidential.",
            **self._common(document, excerpt, visibility=visibility),
        )

    def _stockly_product(self, document: SourceDocumentInput) -> ExtractionPayload:
        product = self._product(
            document,
            "Stockly",
            "stockly.analytos.ai",
            "Pull Kanban inventory intelligence for discrete manufacturing",
            "in_production_pilot_customers",
            "AI-driven Pull Kanban engine that right-sizes kanban loops and safety stock.",
        )
        features = [
            self._feature(document, "Stockly", "Pull Kanban engine", "Digital kanban loops per SKU/work-center with automatic card sizing."),
            self._feature(document, "Stockly", "Monte Carlo safety-stock simulation", "Runs demand and lead-time scenarios nightly to recommend safety stock."),
            self._feature(document, "Stockly", "Demand-shift detection", "Flags changed SKU consumption patterns and proposes loop adjustments."),
            self._feature(document, "Stockly", "ERP integration", "Connectors for NetSuite and SAP Business One."),
            self._feature(document, "Stockly", "Autonomy tiers", "Recommend-only, auto-adjust with approval, and autonomous replenishment signals."),
            self._feature(document, "Stockly", "Supplier lead-time intelligence", "Learns actual versus quoted supplier lead times."),
        ]
        proofs = [
            self._proof(document, "Stockly", "21 percent inventory reduction", "on_hand_inventory_reduction", "21%", "21% reduction in on-hand inventory value within 90 days."),
            self._proof(document, "Stockly", "35 percent fewer stockouts", "stockout_reduction", "35%", "35% fewer stockout events within 90 days."),
            self._proof(document, "Stockly", "planner review time under one hour", "planner_review_time", "under 1 hour/week", "Inventory planner time cut from 6 hours/week to under 1 hour/week."),
        ]
        edges = [self._edge("HasFeature", product.slug, f.slug, document, f.name) for f in features]
        edges += [self._edge("ProvenBy", product.slug, p.slug, document, p.name) for p in proofs]
        return ExtractionPayload(nodes=[product, *features, *proofs], edges=edges)

    def _inspectly_product(self, document: SourceDocumentInput) -> ExtractionPayload:
        product = self._product(
            document,
            "Inspectly",
            "inspectly.analytos.ai",
            "Engineering drawing to inspection plan automation",
            "in_production_customer",
            "Reads engineering drawings and generates ballooned inspection plan workbooks.",
        )
        features = [
            self._feature(document, "Inspectly", "Automated dimension extraction", "Extracts dimensions, tolerances, GD&T symbols, notes, and title-block metadata."),
            self._feature(document, "Inspectly", "Balloon numbering", "Auto-balloons each characteristic and keeps numbers consistent across revisions."),
            self._feature(document, "Inspectly", "Excel inspection plan generation", "Outputs customer inspection plan templates ready for FAI/PPAP packages."),
            self._feature(document, "Inspectly", "Revision diffing", "Highlights changed characteristics between revisions."),
            self._feature(document, "Inspectly", "Human verification step", "Routes extracted plans to a quality engineer for review before release."),
        ]
        proofs = [
            self._proof(document, "Inspectly", "inspection plan under 20 minutes", "inspection_plan_time", "under 20 minutes", "Inspection plan creation reduced from 4-6 hours per part to under 20 minutes."),
            self._proof(document, "Inspectly", "92 percent extraction accuracy", "first_pass_accuracy", "92%", "92% first-pass dimension extraction accuracy."),
            self._proof(document, "Inspectly", "regulated quality context support", "quality_contexts", "ISO 13485 and AS9100", "Supports ISO 13485 and AS9100 quality documentation contexts."),
        ]
        edges = [self._edge("HasFeature", product.slug, f.slug, document, f.name) for f in features]
        edges += [self._edge("ProvenBy", product.slug, p.slug, document, p.name) for p in proofs]
        return ExtractionPayload(nodes=[product, *features, *proofs], edges=edges)

    def _icp(self, document: SourceDocumentInput) -> ExtractionPayload:
        segments = [
            ICPSegment(
                slug="icp:mid-market-discrete-manufacturers",
                name="Mid-Market Discrete Manufacturers",
                segment_type="direct",
                revenue_range="$50M-$500M",
                employee_range="100-2,000",
                plant_range="1-6 plants",
                sectors="precision machining, medical device manufacturing, industrial equipment, packaging, automotive tier-2 suppliers, electronics assembly, aerospace suppliers",
                erp_footprint="NetSuite or SAP Business One preferred; Epicor/Infor acceptable",
                geography="US Midwest/Southeast first, then EU",
                trigger_signals="Kanban on cards or Excel, working-capital pressure, hiring planners or quality engineers, ISO 13485/AS9100, NetStock evaluation or churn",
                disqualifiers="Process manufacturing, revenue under $30M, Fortune 500, homegrown ERP without API access",
                status="active",
                **self._common(document, "Segment 1 - Mid-Market Discrete Manufacturers"),
            ),
            ICPSegment(
                slug="icp:pe-firms-and-operating-partners",
                name="PE Firms & Operating Partners",
                segment_type="multiplier_channel",
                trigger_signals="Lower-middle-market PE funds with 3+ manufacturing portfolio companies",
                channel_notes="Build once, deploy across the portfolio.",
                value_framing="EBITDA improvement via working capital release and quality-team productivity.",
                status="active",
                **self._common(document, "Segment 2 - PE Firms & Operating Partners"),
            ),
        ]
        personas = [
            Persona(slug="persona:plant-manager", name="Plant Manager", role_in_deal="Champion", product_focus="Stockly", cares_about="Stockouts, expediting chaos, floor discipline", winning_message="Fewer stockouts, less firefighting, your planners get their week back", **self._common(document, "Plant Manager persona")),
            Persona(slug="persona:supply-chain-director", name="Supply Chain Director", role_in_deal="Champion/buyer", product_focus="Stockly", cares_about="Inventory turns, working capital", winning_message="21% inventory reduction in 90 days at a shop like yours", **self._common(document, "Supply Chain Director persona")),
            Persona(slug="persona:quality-manager-engineer", name="Quality Manager / Engineer", role_in_deal="Champion", product_focus="Inspectly", cares_about="Audit readiness, documentation backlog", winning_message="4-6 hours per inspection plan down to 20 minutes, engineer stays in the loop", **self._common(document, "Quality Manager / Engineer persona")),
            Persona(slug="persona:cfo-pe-operating-partner", name="CFO / PE Operating Partner", role_in_deal="Economic buyer", product_focus="Stockly and Inspectly", cares_about="EBITDA, capex vs opex, risk", winning_message="Working capital release plus perpetual license, 2-week POC proof", **self._common(document, "CFO / PE Operating Partner persona")),
        ]
        edges = [
            self._edge("Targets", "product:stockly", segments[0].slug, document, "Stockly ICP segment"),
            self._edge("Targets", "product:inspectly", segments[0].slug, document, "Inspectly ICP segment"),
            self._edge("Targets", "product:stockly", segments[1].slug, document, "PE channel segment"),
            self._edge("Targets", "product:inspectly", segments[1].slug, document, "PE channel segment"),
            *[self._edge("HasPersona", segments[0].slug, p.slug, document, p.name) for p in personas],
            self._edge("HasPersona", segments[1].slug, personas[3].slug, document, personas[3].name),
        ]
        return ExtractionPayload(nodes=[*segments, *personas], edges=edges)

    def _people(self, document: SourceDocumentInput) -> list[Person]:
        return [
            Person(slug="person:santosh-thota", name="Santosh Thota", email="santosh@analytos.ai", organization="Analytos", person_type="internal", **self._common(document, "Santosh Thota")),
            Person(slug="person:narayan-laksham", name="Narayan Laksham", email="narayan@analytos.ai", organization="Analytos", person_type="internal", **self._common(document, "Narayan Laksham")),
            Person(slug="person:ashok-suthar", name="Ashok Suthar", email="ashok@analytos.ai", organization="Analytos", person_type="internal", **self._common(document, "Ashok Suthar")),
        ]

    def _email_thread(self, document: SourceDocumentInput, product: str, subject: str, summary: str, date: str) -> EmailThread:
        return EmailThread(
            slug=f"email-thread:{slugify(document.path.stem)}",
            subject=subject,
            thread_date=date,
            participants="Santosh Thota, Narayan Laksham, Ashok Suthar",
            summary=summary,
            status="pending_review",
            sensitivity="internal",
            **self._common(document, summary, visibility="internal"),
        )

    def _stockly_email(self, document: SourceDocumentInput) -> ExtractionPayload:
        thread = self._email_thread(document, "Stockly", "Stockly pilot - 90-day numbers are in", "Internal Stockly pilot result and positioning discussion.", "2026-06-15")
        decisions = [
            Decision(slug="decision:stockly-client-anonymity", title="Keep Stockly pilot client anonymous", decision_type="confidentiality", status="decided", decision_date="2026-06-15", external_approval_status="approved_anonymous", **self._common(document, "keep the client anonymous")),
            Decision(slug="decision:stockly-netstock-displacement", title="Use Pull Kanban plus Monte Carlo versus forecast-push", decision_type="positioning", status="decided", decision_date="2026-06-15", external_approval_status="approved", **self._common(document, "Pull Kanban + Monte Carlo beats forecast-push planning")),
            Decision(slug="decision:stockly-prioritize-netsuite-pilots", title="Prioritize NetSuite shops for next pilots", decision_type="gtm_priority", status="decided", decision_date="2026-06-15", external_approval_status="internal_only", **self._common(document, "next pilot candidates should be NetSuite shops first")),
        ]
        proof = self._proof(document, "Stockly", "supplier lead-time gaps", "supplier_lead_time_gap", "9 days", "Quoted vs actual lead time gaps averaged 9 days on top 50 suppliers.", approved="false", visibility="internal")
        edges = [self._edge("Discusses", thread.slug, "product:stockly", document, "Stockly pilot discussion")]
        edges += [self._edge("DiscussedIn", d.slug, thread.slug, document, d.title) for d in decisions]
        edges += [self._edge("DecidedBy", d.slug, "person:narayan-laksham", document, d.title) for d in decisions]
        edges += [self._edge("SupportedBy", "feature:stockly:supplier-lead-time-intelligence", proof.slug, document, proof.name)]
        return ExtractionPayload(nodes=[thread, *self._people(document), *decisions, proof], edges=edges)

    def _inspectly_email(self, document: SourceDocumentInput) -> ExtractionPayload:
        thread = self._email_thread(document, "Inspectly", "Inspectly - 4 parts processed, verification loop working", "Internal Inspectly medical device expansion discussion.", "2026-06-18")
        decisions = [
            Decision(slug="decision:inspectly-client-confidentiality", title="Keep Inspectly client name confidential", decision_type="confidentiality", status="decided", decision_date="2026-06-18", external_approval_status="approved_anonymous", **self._common(document, "Client name stays confidential")),
            Decision(slug="decision:inspectly-human-in-loop-positioning", title="Position verification as human-in-the-loop", decision_type="positioning", status="decided", decision_date="2026-06-18", external_approval_status="approved", **self._common(document, "engineer stays in the loop")),
            Decision(slug="decision:inspectly-aerospace-expansion", title="Prioritize aerospace suppliers doing FAI packages", decision_type="gtm_priority", status="decided", decision_date="2026-06-18", external_approval_status="internal_only", **self._common(document, "aerospace suppliers doing FAI packages")),
        ]
        proof = self._proof(document, "Inspectly", "revision diff seven changed characteristics", "revision_diff_scope", "7 of 140", "Revision diff highlighted 7 changed characteristics out of 140.", approved="false", visibility="internal")
        edges = [self._edge("Discusses", thread.slug, "product:inspectly", document, "Inspectly expansion discussion")]
        edges += [self._edge("DiscussedIn", d.slug, thread.slug, document, d.title) for d in decisions]
        edges += [self._edge("DecidedBy", d.slug, "person:narayan-laksham", document, d.title) for d in decisions]
        edges += [self._edge("SupportedBy", "feature:inspectly:revision-diffing", proof.slug, document, proof.name)]
        return ExtractionPayload(nodes=[thread, *self._people(document), *decisions, proof], edges=edges)


class ConfigurableLLMExtractor(BaseExtractor):
    def __init__(self, provider: str, model_name: str, api_key: str):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key

    def extract(self, document: SourceDocumentInput) -> ExtractionPayload:
        raise RuntimeError(
            "LLM extraction is configured but no provider adapter is implemented yet. "
            "Use EXTRACTION_PROVIDER=rule-based for local tests."
        )


def build_extractor(provider: str, llm_provider: str = "", llm_model: str = "", llm_api_key: str = "") -> BaseExtractor:
    if provider in {"rule-based", "mock"}:
        return RuleBasedExtractor()
    if provider == "llm":
        if not llm_provider or not llm_model or not llm_api_key:
            raise RuntimeError("LLM_PROVIDER, LLM_MODEL, and LLM_API_KEY are required for EXTRACTION_PROVIDER=llm")
        return ConfigurableLLMExtractor(llm_provider, llm_model, llm_api_key)
    raise RuntimeError(f"Unknown EXTRACTION_PROVIDER: {provider}")
