import type {
  ApprovalRequest,
  ContentAgentResult,
  GTMAgentResult,
  GraphRecord,
  HealthResponse,
  IngestionRequest,
  ProductDetail,
  RecentChanges,
  RejectionRequest,
  ReviewDetail,
  SearchResult,
  WorkflowRun
} from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const DEFAULT_TIMEOUT_MS = 15000;

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

async function request<T>(path: string, options: RequestInit = {}, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      }
    });
    const text = await response.text();
    const data = text ? safeJson(text) : null;
    if (!response.ok) {
      const detail = typeof data === "object" && data !== null && "detail" in data ? (data as { detail: unknown }).detail : data;
      throw new ApiError(formatError(detail, response.status), response.status, detail);
    }
    return data as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The API request timed out.", 408, null);
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
  }
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function formatError(detail: unknown, status: number): string {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && "message" in detail) return String((detail as { message: unknown }).message);
  return `API request failed with status ${status}`;
}

export const api = {
  baseUrl: API_BASE_URL,
  health: () => request<HealthResponse>("/health"),
  ingestions: (status?: string) => request<WorkflowRun[]>(status ? `/ingestions?status=${encodeURIComponent(status)}` : "/ingestions"),
  createIngestion: (payload: IngestionRequest) => request<WorkflowRun>("/ingestions", { method: "POST", body: JSON.stringify(payload) }, 30000),
  ingestion: (runId: string) => request<WorkflowRun>(`/ingestions/${encodeURIComponent(runId)}`),
  reviews: () => request<WorkflowRun[]>("/reviews"),
  review: (runId: string) => request<ReviewDetail>(`/reviews/${encodeURIComponent(runId)}`),
  approve: (runId: string, payload: ApprovalRequest) =>
    request<{ run: WorkflowRun; diff: ReviewDetail; merge_result: unknown }>(`/reviews/${encodeURIComponent(runId)}/approve`, {
      method: "POST",
      body: JSON.stringify(payload)
    }, 30000),
  reject: (runId: string, payload: RejectionRequest) =>
    request<WorkflowRun>(`/reviews/${encodeURIComponent(runId)}/reject`, { method: "POST", body: JSON.stringify(payload) }, 30000),
  entities: (path: string) => request<GraphRecord[]>(path),
  productDetail: (slug: string) => request<ProductDetail>(`/entities/products/${encodeURIComponent(slug)}`),
  search: (query: string) => request<SearchResult[]>(`/search?q=${encodeURIComponent(query)}`),
  recentChanges: () => request<RecentChanges>("/changes/recent"),
  contentAgent: (topic: string, actor = "content-agent") =>
    request<ContentAgentResult>("/agents/content", { method: "POST", body: JSON.stringify({ topic, actor }) }, 30000),
  gtmAgent: (product: string, actor = "gtm-agent") =>
    request<GTMAgentResult>("/agents/gtm", { method: "POST", body: JSON.stringify({ product, actor }) }, 30000)
};

export function isNotImplemented(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

export function isInsufficientEvidence(error: unknown): boolean {
  return error instanceof ApiError && error.status === 409;
}
