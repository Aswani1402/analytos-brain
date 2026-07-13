import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { HealthResponse, RecentChanges, WorkflowRun } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";

const seedPaths = [
  "seed-data/stockly-product-overview.md",
  "seed-data/inspectly-product-overview.md",
  "seed-data/icp-analytos.md",
  "seed-data/email-01-stockly-pilot-thread.md",
  "seed-data/email-02-inspectly-medical-thread.md"
];

export function OverviewPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [reviews, setReviews] = useState<WorkflowRun[]>([]);
  const [changes, setChanges] = useState<RecentChanges | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sourcePath, setSourcePath] = useState(seedPaths[0]);
  const [actor, setActor] = useState("ingestion-service");
  const [provider, setProvider] = useState("rule-based");
  const [creating, setCreating] = useState(false);
  const [createdRun, setCreatedRun] = useState<WorkflowRun | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([api.health(), api.ingestions(), api.reviews(), api.recentChanges()])
      .then(([healthResult, runResult, reviewResult, changeResult]) => {
        if (!active) return;
        setHealth(healthResult);
        setRuns(runResult);
        setReviews(reviewResult);
        setChanges(changeResult);
        setError(null);
      })
      .catch((err) => active && setError(err instanceof Error ? err.message : "Unable to reach the API"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  const approvedCount = useMemo(() => runs.filter((run) => run.status === "approved").length, [runs]);

  async function submitIngestion(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    setCreateError(null);
    setCreatedRun(null);
    try {
      const run = await api.createIngestion({ source_path: sourcePath, actor, extraction_provider: provider });
      setCreatedRun(run);
      setReviews((current) => (run.status === "pending_review" ? [run, ...current] : current));
      setRuns((current) => [run, ...current]);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Ingestion failed");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>Overview</h1>
        </div>
      </div>

      {loading ? <LoadingState label="Checking services" /> : null}
      {error ? <ErrorState message={`API unreachable: ${error}`} /> : null}

      {health ? (
        <div className="metric-grid">
          <Metric label="API" value={health.api.ok ? "online" : "offline"} />
          <Metric label="SQLite" value={health.sqlite.ok ? "online" : "offline"} />
          <Metric label="Omnigraph" value={health.omnigraph.ok ? "online" : "offline"} />
          <Metric label="Pending reviews" value={String(reviews.length)} />
          <Metric label="Approved ingestions" value={String(approvedCount)} />
        </div>
      ) : null}

      <section className="panel">
        <div className="section-heading">
          <h2>Create ingestion</h2>
          <StatusBadge value="pending_review" />
        </div>
        <form className="form-grid" onSubmit={submitIngestion}>
          <label>
            Source path
            <input value={sourcePath} onChange={(event) => setSourcePath(event.target.value)} />
          </label>
          <label>
            Actor
            <input value={actor} onChange={(event) => setActor(event.target.value)} />
          </label>
          <label>
            Extraction provider
            <input value={provider} onChange={(event) => setProvider(event.target.value)} />
          </label>
          <div className="quick-select">
            {seedPaths.map((path) => (
              <button type="button" key={path} onClick={() => setSourcePath(path)}>
                {path.replace("seed-data/", "")}
              </button>
            ))}
          </div>
          <button className="primary-action" disabled={creating} type="submit">
            {creating ? "Creating" : "Create review branch"}
          </button>
        </form>
        {createError ? <ErrorState message={createError} /> : null}
        {createdRun ? (
          <div className="result-panel">
            <p>
              Run <strong>{createdRun.run_id}</strong> is <StatusBadge value={createdRun.status} /> on branch{" "}
              <strong>{createdRun.branch_name}</strong>.
            </p>
            <p>Data remains pending until review approval.</p>
            <Link to={`/reviews/${encodeURIComponent(createdRun.run_id)}`}>Open review</Link>
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>Recent activity</h2>
          <Link to="/changes">View all</Link>
        </div>
        {!changes || changes.workflow_actions.length === 0 ? <EmptyState message="No workflow activity" /> : null}
        <div className="activity-list">
          {changes?.workflow_actions.slice(0, 5).map((action) => (
            <article key={action.id} className="activity-row">
              <StatusBadge value={action.action} />
              <span>{action.actor}</span>
              <time>{formatDate(action.created_at)}</time>
              {action.run_id ? <Link to={`/reviews/${encodeURIComponent(action.run_id)}`}>{action.run_id}</Link> : null}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <article className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
