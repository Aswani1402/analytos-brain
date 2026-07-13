import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { RecentChanges } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";

export function RecentChangesPage() {
  const [changes, setChanges] = useState<RecentChanges | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .recentChanges()
      .then(setChanges)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load changes"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Audit</p>
          <h1>Recent Changes</h1>
        </div>
      </div>
      {loading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {changes ? (
        <>
          <section className="panel">
            <div className="section-heading">
              <h2>Workflow actions</h2>
              <span className="count-pill">{changes.workflow_actions.length}</span>
            </div>
            {changes.workflow_actions.length === 0 ? <EmptyState message="No workflow actions" /> : null}
            <div className="activity-list">
              {changes.workflow_actions.map((action) => (
                <article className="activity-row" key={action.id}>
                  <StatusBadge value={action.action} />
                  <span>{action.actor}</span>
                  <time>{formatDate(action.created_at)}</time>
                  {action.run_id ? <Link to={`/reviews/${encodeURIComponent(action.run_id)}`}>{action.run_id}</Link> : null}
                  <code>{JSON.stringify(action.details)}</code>
                </article>
              ))}
            </div>
          </section>
          <section className="panel">
            <div className="section-heading">
              <h2>Omnigraph commits</h2>
              <span className="count-pill">{changes.commits.length}</span>
            </div>
            {changes.commits.length === 0 ? <EmptyState message="No main commit records returned" /> : null}
            <div className="compact-list">
              {changes.commits.map((commit, index) => (
                <article className="compact-row" key={index}>
                  <pre>{JSON.stringify(commit, null, 2)}</pre>
                </article>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
