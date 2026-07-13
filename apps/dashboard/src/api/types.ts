export type JsonMap = Record<string, unknown>;

export interface HealthResponse {
  api: { ok: boolean; name: string };
  sqlite: { ok: boolean; path: string; error?: string };
  omnigraph: { ok: boolean; graph_uri: string; version?: string; branches?: string[]; error?: string };
}

export interface WorkflowRun {
  run_id: string;
  source_path: string;
  source_document_hash: string;
  branch_name: string;
  extraction_provider: string;
  extraction_model: string;
  ingestion_actor?: string;
  status: "extracting" | "pending_review" | "approved" | "rejected" | "failed" | string;
  created_at: string;
  reviewer_actor?: string | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
  merge_result?: JsonMap | null;
  summary: Record<string, unknown>;
  jsonl_path: string;
  error_message?: string | null;
  review_url?: string;
}

export interface GraphRecord {
  type?: string;
  edge?: string;
  from?: string;
  to?: string;
  data: JsonMap;
}

export interface ChangeRecord {
  before: GraphRecord;
  after: GraphRecord;
}

export interface ReviewDetail {
  run: WorkflowRun;
  source_document: { path: string; content: string | null; hash: string };
  branch_name: string;
  added_nodes?: GraphRecord[];
  changed_nodes?: ChangeRecord[];
  removed_nodes?: GraphRecord[];
  added_edges?: GraphRecord[];
  changed_edges?: ChangeRecord[];
  removed_edges?: GraphRecord[];
  counts?: {
    nodes: number;
    edges: number;
    by_node_type: Record<string, number>;
    by_edge_type: Record<string, number>;
  };
  confidence?: string[];
  provenance?: JsonMap[];
  visibility?: Record<string, number>;
}

export interface IngestionRequest {
  source_path: string;
  actor: string;
  extraction_provider: string;
}

export interface ApprovalRequest {
  reviewer_actor: string;
}

export interface RejectionRequest {
  reviewer_actor: string;
  reason: string;
}

export interface ProductDetail {
  product: JsonMap;
  features: JsonMap[];
  proof_points: JsonMap[];
  icp_segments: JsonMap[];
}

export interface SearchResult {
  node_type: string;
  slug: string | null;
  matched_text: string;
  visibility?: string;
  provenance?: JsonMap;
}

export interface RecentChanges {
  commits: JsonMap[];
  workflow_actions: Array<{
    id: number;
    run_id: string | null;
    actor: string;
    action: string;
    created_at: string;
    details: JsonMap;
  }>;
}

export interface AgentFact {
  slug: string;
  name: string;
  fact: string;
}

export interface ContentAgentResult {
  title: string;
  blog_draft: string;
  draft: string;
  facts_used: AgentFact[];
  graph_node_slugs: string[];
  source_documents: string[];
  graph_evidence: GraphRecord[];
  generation_mode: string;
}

export interface GTMAgentResult {
  target_company_profile: JsonMap;
  persona_to_contact: JsonMap;
  competitor_or_displacement_angle: string;
  illustrative_companies: Array<{ name: string; label: string }>;
  grounded_opening_angle: string;
  approved_proof_points_used: AgentFact[];
  graph_node_slugs: string[];
  source_documents: string[];
  graph_evidence: GraphRecord[];
  generation_mode: string;
}
