import type { JsonMap } from "../api/types";

const provenanceKeys = ["source_file", "source_path", "source_document_id", "source_excerpt", "evidence", "confidence", "visibility"];

export function ProvenancePanel({ data }: { data: JsonMap }) {
  const entries = provenanceKeys
    .map((key) => [key, data[key]] as const)
    .filter(([, value]) => value !== undefined && value !== null && value !== "");

  if (entries.length === 0) return null;

  return (
    <dl className="provenance">
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
