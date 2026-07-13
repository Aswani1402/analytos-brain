# Analytos Brain Graph Schema

This document describes the typed Omnigraph model used for the local Analytos Brain knowledge graph. The graph is designed to hold product, ICP, proof point, email, decision, source-document, and extraction-run knowledge while keeping internal material separate from externally approved claims.

## Deterministic Slugs

Every node has a deterministic `slug: String` and declares `@key(slug)`. Omnigraph owns the internal `id`; loaders must never write a custom `id` property.

Recommended slug conventions:

- `product:<product-name>` for products, such as `product:stockly`
- `feature:<product-name>:<feature-name>` for features
- `proof:<product-name>:<short-claim>` for proof points
- `icp:<segment-name>` for ICP segments
- `persona:<persona-name>` for personas
- `person:<email-or-name>` for named people
- `email-thread:<source-file-stem>` for email threads
- `decision:<source-file-stem>:<short-decision>` for decisions
- `source-document:<file-name>` for source documents
- `extraction-run:<branch-name>` for extraction runs

Use lowercase ASCII, replace spaces with hyphens, and keep the slug stable across branches and reruns.

## Scalar Conventions

The local Omnigraph 0.8.1 parser accepted nullable strings and rejected enum, float, boolean, and integer schema types during validation. Controlled and numeric values are therefore stored as indexed strings:

- `visibility`: `internal`, `external_approved`, or `restricted`
- `status`: domain-specific lifecycle value, such as `active`, `draft`, `processed`, or `approved`
- `approved_for_external_use`: `true` or `false`
- `confidence`: decimal text such as `0.92`
- `source_count`: integer text such as `5`

## Provenance

Domain nodes include provenance fields where applicable:

- `source_document_id`
- `source_file`
- `source_excerpt`
- `confidence`
- `visibility`
- `created_at`
- `updated_at`

Relationships include edge-level provenance:

- `source_document_id`
- `source_file`
- `source_excerpt`
- `confidence`
- `created_at`

This lets the graph distinguish what an entity means from where a specific assertion came from. For example, a product can be sourced from a product overview while a proof point can be sourced from an email thread and marked external-approved only after human review.

## Node Types

### Product

Represents products such as Stockly and Inspectly. It stores site URL, category, owner, lifecycle status, positioning, competitive alternatives, technical stack, and target buyer notes.

### Feature

Represents product capabilities, including kanban loops, Monte Carlo simulation, demand-shift detection, ERP integration, dimension extraction, balloon numbering, Excel plan generation, revision diffing, and human verification.

### ProofPoint

Represents evidence, metrics, and claims. It records proof type, metric fields, baseline, result, timeframe, customer segment, confidentiality notes, and `approved_for_external_use`. This separates public proof points from internal-only email details.

### Persona

Represents buyer and champion personas from the ICP document, including role in deal, product focus, cares-about text, losing message, winning message, and economic role.

### ICPSegment

Represents target segments such as mid-market discrete manufacturers and PE firms or operating partners. It captures firmographics, sectors, ERP fit, geography, trigger signals, disqualifiers, channel notes, and value framing.

### Person

Represents named people appearing in owner fields and email threads, such as Narayan Laksham, Santosh Thota, and Ashok Suthar. It stores email, organization, role, person type, visibility, and provenance.

### EmailThread

Represents internal email threads. Email threads are internal by default via `visibility` and `sensitivity`, and should not be treated as externally approved content without a linked proof point or decision that explicitly says so.

### Decision

Represents explicit decisions and GTM guidance from the source documents and email threads, such as client anonymity, approved proof-point wording, positioning, priority integrations, and expansion targeting.

### SourceDocument

Represents each seed or future source file. It stores file name, document type, title, content hash, visibility, and provenance fields so extraction output can be traced back to exact inputs.

### ExtractionRun

Represents a branch-based extraction attempt. It stores branch name, model name, prompt version, status, timestamps, source count, notes, visibility, and provenance.

## Edge Types

### Product -HasFeature-> Feature

Connects products to their capabilities. The edge is unique per product-feature pair.

### Product -ProvenBy-> ProofPoint

Connects a product to evidence that supports product-level claims. The edge is unique per product-proof pair.

### Feature -SupportedBy-> ProofPoint

Connects specific features to supporting proof, such as revision diffing evidence or supplier lead-time findings. The edge is unique per feature-proof pair.

### Product -Targets-> ICPSegment

Connects products to target market segments. The edge is unique per product-segment pair.

### ICPSegment -HasPersona-> Persona

Connects ICP segments to relevant personas. The edge is unique per segment-persona pair.

### EmailThread -Discusses-> Product

Connects internal email discussions to products. The edge is unique per thread-product pair.

### Decision -DiscussedIn-> EmailThread

Connects decisions to the email thread where they were discussed. The edge is unique per decision-thread pair.

### Decision -DecidedBy-> Person

Connects decisions to the person who made or confirmed them. The edge is unique per decision-person pair.

### ExtractionRun -Processed-> SourceDocument

Connects extraction runs to the source documents they processed. The edge is unique per run-document pair.

## Visibility And External Approval

`visibility` separates internal source material from approved external claims. Product overviews and ICP notes are internal unless a loader explicitly marks a derived claim as approved. `EmailThread` records should remain `internal` by default. `ProofPoint.approved_for_external_use` is the field that determines whether a proof point can be used externally; a proof point can still carry a restricted or anonymized external label.

Examples:

- Stockly pilot metrics can be approved externally while preserving anonymous client wording.
- Inspectly proof points can be approved externally while keeping the medical device customer name confidential.
- Technical stacks and internal email thread content should remain internal unless reviewed and transformed into an approved proof point.

## Branch-Based Human Review

Extraction runs on a temporary flat branch named `ing-<timestamp>-<document-slug>-<document-hash-prefix>-<uuid-suffix>`, for example `ing-20260713091530012345-stockly-prod-a1b2c3d4-9f8e7d6c5b4a`. The timestamp is UTC in `YYYYMMDDHHMMSSffffff` format. The document slug is derived from the source file stem with the same lowercase ASCII slug rules used for business identifiers and is capped at 12 characters to keep Omnigraph manifest paths below common Windows path-length limits. The document-hash prefix is the first 8 characters of the source document SHA-256 and keeps the branch traceable to the exact input content. The UUID suffix is 12 lowercase hex characters and makes separate ingestion attempts unique even for the same document and timestamp. A flat branch name is used instead of a slash-delimited name so Windows paths and shell tooling never interpret branch components as directories. Every ingestion receives a separate branch from `main` so extracted knowledge remains isolated for review and cannot overwrite approved main knowledge directly.

Each ingestion branch writes `ExtractionRun` and `SourceDocument` records plus extracted domain nodes and edges. Reviewers can inspect diffs, query the branch, approve or reject proof-point visibility, and only then merge into `main`.

The schema supports this workflow by making extraction provenance first-class and by keeping relationship provenance on edges. Human reviewers can see exactly which file and excerpt created each claim before accepting it into the main graph.

## Stored Read Queries

The cluster registers read queries for the review dashboard, API, MCP wrapper, and agents:

- `list_products`
- `get_product`
- `get_product_features`
- `get_product_proof_points`
- `get_product_icp_segments`
- `list_features`
- `list_proof_points`
- `list_icp_segments`
- `list_personas`
- `list_people`
- `list_email_threads`
- `list_decisions`
- `list_source_documents`
- `list_extraction_runs`
- `search_entities`
- `recent_changes`

Product context is split across `get_product`, `get_product_features`, `get_product_proof_points`, and `get_product_icp_segments`. Omnigraph 0.8.1 query validation in this repo does not provide a documented optional-match or union example, so the API layer should combine these separate results. This keeps partial context retrievable when a product has features but no proof points, proof points but no ICP edges, or any other incomplete relationship set.

`search_entities` is deliberately narrow in this first Omnigraph 0.8.1-compatible version: it resolves a product by deterministic slug. Broader cross-type search belongs in the API layer, where the backend can fan out to type-specific graph queries without relying on unsupported query-language union behavior.

`recent_changes` is modeled as a recent-ingestion feed over `ExtractionRun` records. It stays empty until the ingestion pipeline writes reviewed branch metadata.
