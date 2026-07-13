import type { ChangeRecord, GraphRecord, JsonMap } from "../api/types";
import { EmptyState } from "./EmptyState";
import { ProvenancePanel } from "./ProvenancePanel";
import { StatusBadge } from "./StatusBadge";

interface DiffSectionProps {
  title: string;
  records?: GraphRecord[];
  changes?: ChangeRecord[];
}

const hiddenKeys = new Set(["id"]);

export function DiffSection({ title, records = [], changes = [] }: DiffSectionProps) {
  const hasContent = records.length > 0 || changes.length > 0;
  return (
    <section className="diff-section">
      <div className="section-heading">
        <h2>{title}</h2>
        <span className="count-pill">{records.length + changes.length}</span>
      </div>
      {!hasContent ? <EmptyState message="No records" /> : null}
      <div className="diff-list">
        {records.map((record, index) => (
          <DiffRecord key={`${title}-record-${index}`} record={record} />
        ))}
        {changes.map((change, index) => (
          <article className="diff-record" key={`${title}-change-${index}`}>
            <DiffRecordHeader record={change.after} />
            <div className="compare-grid">
              <div>
                <h4>Before</h4>
                <PropertyList data={change.before.data} />
              </div>
              <div>
                <h4>After</h4>
                <PropertyList data={change.after.data} />
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function DiffRecord({ record }: { record: GraphRecord }) {
  return (
    <article className="diff-record">
      <DiffRecordHeader record={record} />
      <PropertyList data={record.data} />
      <ProvenancePanel data={record.data} />
    </article>
  );
}

function DiffRecordHeader({ record }: { record: GraphRecord }) {
  const slug = typeof record.data.slug === "string" ? record.data.slug : null;
  return (
    <div className="diff-record-header">
      <div>
        <p className="eyebrow">{record.type || record.edge || "record"}</p>
        {record.edge ? <h3>{`${record.from || "unknown"} -> ${record.to || "unknown"}`}</h3> : <h3>{slug || "record"}</h3>}
      </div>
      <div className="badge-row">
        {record.data.visibility ? <StatusBadge value={String(record.data.visibility)} /> : null}
        {record.data.confidence ? <StatusBadge value={String(record.data.confidence)} /> : null}
      </div>
    </div>
  );
}

function PropertyList({ data }: { data: JsonMap }) {
  const entries = Object.entries(data)
    .filter(([key, value]) => !hiddenKeys.has(key) && value !== undefined && value !== null && value !== "")
    .slice(0, 12);

  return (
    <dl className="property-list">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt>{key.replace(/_/g, " ")}</dt>
          <dd>{formatValue(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return value.map(formatValue).join(", ");
  if (value && typeof value === "object") return JSON.stringify(value);
  return String(value);
}
