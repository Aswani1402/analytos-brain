import { Link } from "react-router-dom";
import type { GraphRecord, JsonMap } from "../api/types";
import { ProvenancePanel } from "./ProvenancePanel";
import { StatusBadge } from "./StatusBadge";

interface EntityCardProps {
  record: GraphRecord | JsonMap;
  detailPath?: string;
}

export function EntityCard({ record, detailPath }: EntityCardProps) {
  const graphRecord = isGraphRecord(record) ? record : null;
  const data = graphRecord ? graphRecord.data : (record as JsonMap);
  const type = graphRecord?.type || (data.node_type as string | undefined);
  const slug = typeof data.slug === "string" ? data.slug : null;
  const title = pickText(data, ["name", "title", "subject", "label", "slug"]) || "Untitled";
  const summary = pickText(data, ["summary", "description", "body", "matched_text"]);

  return (
    <article className="entity-card">
      <div className="entity-card-header">
        <div>
          <p className="eyebrow">{type || "entity"}</p>
          <h3>{detailPath && slug ? <Link to={`${detailPath}/${encodeURIComponent(slug)}`}>{title}</Link> : title}</h3>
        </div>
        <div className="badge-row">
          {data.visibility ? <StatusBadge value={String(data.visibility)} /> : null}
          {data.approved_for_external_use !== undefined ? <StatusBadge value={Boolean(data.approved_for_external_use)} /> : null}
        </div>
      </div>
      {slug ? <p className="slug">{slug}</p> : null}
      {summary ? <p>{summary}</p> : null}
      <ProvenancePanel data={data} />
    </article>
  );
}

function isGraphRecord(record: GraphRecord | JsonMap): record is GraphRecord {
  return typeof (record as GraphRecord).data === "object" && (record as GraphRecord).data !== null;
}

function pickText(data: JsonMap, keys: string[]): string | null {
  for (const key of keys) {
    const value = data[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return null;
}
