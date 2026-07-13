import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { GraphRecord } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { EntityCard } from "../components/EntityCard";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

const entityTypes = [
  { label: "Products", path: "/entities/products" },
  { label: "Features", path: "/entities/features" },
  { label: "Proof Points", path: "/entities/proof-points" },
  { label: "ICP Segments", path: "/entities/icp-segments" },
  { label: "Personas", path: "/entities/personas" },
  { label: "People", path: "/entities/people" },
  { label: "Email Threads", path: "/entities/email-threads" },
  { label: "Decisions", path: "/entities/decisions" }
];

export function EntityBrowserPage() {
  const [selected, setSelected] = useState(entityTypes[0]);
  const [records, setRecords] = useState<GraphRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .entities(selected.path)
      .then(setRecords)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load entities"))
      .finally(() => setLoading(false));
  }, [selected]);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Approved main</p>
          <h1>Entity Browser</h1>
        </div>
      </div>
      <div className="segmented" role="tablist" aria-label="Entity types">
        {entityTypes.map((type) => (
          <button key={type.path} className={type.path === selected.path ? "active" : ""} onClick={() => setSelected(type)} type="button">
            {type.label}
          </button>
        ))}
      </div>
      {loading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!loading && records.length === 0 ? <EmptyState message={`No approved ${selected.label.toLowerCase()}`} /> : null}
      <div className="card-grid">
        {records.map((record, index) => (
          <EntityCard key={`${record.type}-${String(record.data.slug)}-${index}`} record={record} detailPath={selected.path === "/entities/products" ? "/products" : undefined} />
        ))}
      </div>
    </div>
  );
}
