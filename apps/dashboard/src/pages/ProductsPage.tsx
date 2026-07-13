import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { GraphRecord } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { EntityCard } from "../components/EntityCard";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function ProductsPage() {
  const [records, setRecords] = useState<GraphRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .entities("/entities/products")
      .then(setRecords)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load products"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Approved main</p>
          <h1>Products</h1>
        </div>
      </div>
      {loading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {!loading && records.length === 0 ? <EmptyState message="No approved products" /> : null}
      <div className="card-grid">
        {records.map((record) => (
          <EntityCard key={String(record.data.slug)} record={record} detailPath="/products" />
        ))}
      </div>
    </div>
  );
}
