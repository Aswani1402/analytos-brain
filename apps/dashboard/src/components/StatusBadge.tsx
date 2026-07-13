interface StatusBadgeProps {
  value?: string | boolean | null;
}

export function StatusBadge({ value }: StatusBadgeProps) {
  const label = value === true ? "yes" : value === false ? "no" : value || "unknown";
  const normalized = String(label).toLowerCase().replace(/[^a-z0-9]+/g, "-");
  return <span className={`status-badge status-${normalized}`}>{String(label).replace(/_/g, " ")}</span>;
}
