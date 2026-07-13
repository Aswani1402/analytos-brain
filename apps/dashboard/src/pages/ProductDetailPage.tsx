import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { JsonMap, ProductDetail } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ProvenancePanel } from "../components/ProvenancePanel";

export function ProductDetailPage() {
  const { slug } = useParams();
  const [detail, setDetail] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    api
      .productDetail(slug)
      .then(setDetail)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load product"))
      .finally(() => setLoading(false));
  }, [slug]);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Product detail</p>
          <h1>{slug}</h1>
        </div>
        <Link to="/products">Back to products</Link>
      </div>
      {loading ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {detail ? (
        <>
          <section className="panel">
            <h2>{text(detail.product, "name") || slug}</h2>
            <p>{text(detail.product, "description") || text(detail.product, "summary")}</p>
            <ProvenancePanel data={detail.product} />
          </section>
          <RelationSection title="Features" records={detail.features} />
          <RelationSection title="Proof points" records={detail.proof_points} />
          <RelationSection title="Target ICP segments" records={detail.icp_segments} />
        </>
      ) : null}
    </div>
  );
}

function RelationSection({ title, records }: { title: string; records: JsonMap[] }) {
  return (
    <section className="panel">
      <div className="section-heading">
        <h2>{title}</h2>
        <span className="count-pill">{records.length}</span>
      </div>
      {records.length === 0 ? <EmptyState message={`No ${title.toLowerCase()}`} /> : null}
      <div className="compact-list">
        {records.map((record, index) => (
          <article key={`${title}-${index}`} className="compact-row">
            <h3>{text(record, "name") || text(record, "title") || text(record, "slug") || "record"}</h3>
            <p>{text(record, "description") || text(record, "summary") || text(record, "source_excerpt")}</p>
            <ProvenancePanel data={record} />
          </article>
        ))}
      </div>
    </section>
  );
}

function text(data: JsonMap, key: string): string | null {
  const value = data[key];
  return typeof value === "string" && value.trim() ? value : null;
}
