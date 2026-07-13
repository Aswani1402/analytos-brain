import { FormEvent, useState } from "react";
import { api } from "../api/client";
import type { SearchResult } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ProvenancePanel } from "../components/ProvenancePanel";
import { StatusBadge } from "../components/StatusBadge";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      setResults(await api.search(query.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Approved main</p>
          <h1>Search</h1>
        </div>
      </div>
      <form className="search-form" onSubmit={submit}>
        <label>
          Search text
          <input value={query} onChange={(event) => setQuery(event.target.value)} />
        </label>
        <button className="primary-action" type="submit" disabled={loading || !query.trim()}>
          Search
        </button>
      </form>
      {loading ? <LoadingState label="Searching" /> : null}
      {error ? <ErrorState message={error} /> : null}
      {searched && !loading && results.length === 0 ? <EmptyState message="No approved matches" /> : null}
      <div className="compact-list">
        {results.map((result) => (
          <article className="compact-row" key={`${result.node_type}-${result.slug}-${result.matched_text}`}>
            <div className="entity-card-header">
              <div>
                <p className="eyebrow">{result.node_type}</p>
                <h3>{result.slug || "record"}</h3>
              </div>
              {result.visibility ? <StatusBadge value={result.visibility} /> : null}
            </div>
            <p>{result.matched_text}</p>
            {result.provenance ? <ProvenancePanel data={result.provenance} /> : null}
          </article>
        ))}
      </div>
    </div>
  );
}
