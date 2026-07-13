import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { WorkflowRun } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";

export function ReviewsPage() {
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .reviews()
      .then(setRuns)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load reviews"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Human review</p>
          <h1>Pending Reviews</h1>
        </div>
      </div>
      {loading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!loading && runs.length === 0 ? <EmptyState message="No pending reviews" /> : null}
      <div className="table-wrap">
        {runs.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Source</th>
                <th>Branch</th>
                <th>Status</th>
                <th>Provider</th>
                <th>Created</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.run_id}>
                  <td>
                    <Link to={`/reviews/${encodeURIComponent(run.run_id)}`}>{run.run_id}</Link>
                  </td>
                  <td>{run.source_path}</td>
                  <td>{run.branch_name}</td>
                  <td><StatusBadge value={run.status} /></td>
                  <td>{run.extraction_provider}{run.extraction_model ? ` / ${run.extraction_model}` : ""}</td>
                  <td>{formatDate(run.created_at)}</td>
                  <td>{formatSummary(run.summary)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </div>
    </div>
  );
}

function formatSummary(summary: Record<string, unknown>): string {
  return Object.entries(summary)
    .map(([key, value]) => `${key}: ${value}`)
    .join(", ");
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
