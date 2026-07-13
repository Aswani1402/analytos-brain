import type { ReactNode } from "react";
import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { ReviewDetail } from "../api/types";
import { DiffSection } from "../components/DiffSection";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";

export function ReviewDetailPage() {
  const { runId } = useParams();
  const [detail, setDetail] = useState<ReviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [reviewer, setReviewer] = useState("reviewer-demo");
  const [reason, setReason] = useState("");

  async function load() {
    if (!runId) return;
    setLoading(true);
    setError(null);
    try {
      setDetail(await api.review(runId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load review");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [runId]);

  async function approve(event: FormEvent) {
    event.preventDefault();
    if (!runId || !window.confirm("Merge this ingestion branch into approved main?")) return;
    setActionLoading(true);
    setActionMessage(null);
    setError(null);
    try {
      const result = await api.approve(runId, { reviewer_actor: reviewer });
      setActionMessage(`Approved by ${result.run.reviewer_actor || reviewer}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setActionLoading(false);
    }
  }

  async function reject(event: FormEvent) {
    event.preventDefault();
    if (!runId || !reason.trim()) return;
    if (!window.confirm("Discard this ingestion branch?")) return;
    setActionLoading(true);
    setActionMessage(null);
    setError(null);
    try {
      const result = await api.reject(runId, { reviewer_actor: reviewer, reason: reason.trim() });
      setActionMessage(`Rejected by ${result.reviewer_actor || reviewer}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rejection failed");
    } finally {
      setActionLoading(false);
    }
  }

  const pending = detail?.run.status === "pending_review";

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Review detail</p>
          <h1>{runId}</h1>
        </div>
        <Link to="/reviews">Back to reviews</Link>
      </div>
      {loading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {actionMessage ? <div className="state state-success">{actionMessage}</div> : null}
      {detail ? (
        <>
          <section className="panel">
            <div className="metadata-grid">
              <Meta label="Status" value={<StatusBadge value={detail.run.status} />} />
              <Meta label="Source" value={detail.run.source_path} />
              <Meta label="Branch" value={detail.branch_name} />
              <Meta label="Hash" value={detail.run.source_document_hash} />
              <Meta label="Created" value={detail.run.created_at} />
              <Meta label="Provider" value={`${detail.run.extraction_provider} ${detail.run.extraction_model || ""}`} />
            </div>
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>Counts</h2>
            </div>
            {detail.counts ? (
              <div className="metadata-grid">
                <Meta label="Nodes" value={String(detail.counts.nodes)} />
                <Meta label="Edges" value={String(detail.counts.edges)} />
                <Meta label="Node types" value={formatMap(detail.counts.by_node_type)} />
                <Meta label="Edge types" value={formatMap(detail.counts.by_edge_type)} />
              </div>
            ) : (
              <EmptyState message="No diff counts" />
            )}
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>Source document</h2>
            </div>
            <pre className="source-preview">{detail.source_document.content || "Source content unavailable"}</pre>
          </section>

          <DiffSection title="Added nodes" records={detail.added_nodes} />
          <DiffSection title="Changed nodes" changes={detail.changed_nodes} />
          <DiffSection title="Removed nodes" records={detail.removed_nodes} />
          <DiffSection title="Added edges" records={detail.added_edges} />
          <DiffSection title="Changed edges" changes={detail.changed_edges} />
          <DiffSection title="Removed edges" records={detail.removed_edges} />

          <section className="panel action-panel">
            <div className="section-heading">
              <h2>Decision</h2>
              <StatusBadge value={detail.run.status} />
            </div>
            <label>
              Reviewer actor
              <input value={reviewer} onChange={(event) => setReviewer(event.target.value)} disabled={!pending || actionLoading} />
            </label>
            <div className="action-row">
              <form onSubmit={approve}>
                <button className="primary-action" type="submit" disabled={!pending || actionLoading || !reviewer.trim()}>
                  Approve
                </button>
              </form>
              <form className="reject-form" onSubmit={reject}>
                <label>
                  Rejection reason
                  <input value={reason} onChange={(event) => setReason(event.target.value)} disabled={!pending || actionLoading} />
                </label>
                <button type="submit" disabled={!pending || actionLoading || !reviewer.trim() || !reason.trim()}>
                  Reject
                </button>
              </form>
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

function Meta({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="metadata-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatMap(value: Record<string, number>): string {
  return Object.entries(value)
    .map(([key, count]) => `${key}: ${count}`)
    .join(", ");
}
