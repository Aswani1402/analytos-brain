import { FormEvent, useState } from "react";
import { api, isInsufficientEvidence, isNotImplemented } from "../api/client";
import type { GTMAgentResult } from "../api/types";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function GTMAgentPage() {
  const [product, setProduct] = useState("");
  const [actor, setActor] = useState("gtm-agent");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GTMAgentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notImplemented, setNotImplemented] = useState(false);
  const [insufficientEvidence, setInsufficientEvidence] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!product.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setNotImplemented(false);
    setInsufficientEvidence(false);
    try {
      setResult(await api.gtmAgent(product.trim(), actor.trim() || "gtm-agent"));
    } catch (err) {
      if (isNotImplemented(err)) {
        setNotImplemented(true);
      } else if (isInsufficientEvidence(err)) {
        setInsufficientEvidence(true);
      } else {
        setError(err instanceof Error ? err.message : "GTM Agent request failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Agent workspace</p>
          <h1>GTM Agent</h1>
        </div>
      </div>
      <form className="search-form" onSubmit={submit}>
        <label>
          Product
          <input value={product} onChange={(event) => setProduct(event.target.value)} />
        </label>
        <label>
          Actor
          <input value={actor} onChange={(event) => setActor(event.target.value)} />
        </label>
        <button className="primary-action" type="submit" disabled={loading || !product.trim()}>
          Submit
        </button>
      </form>
      {loading ? <LoadingState label="Requesting agent" /> : null}
      {notImplemented ? <div className="state state-empty">Agent backend not yet implemented.</div> : null}
      {insufficientEvidence ? <div className="state state-empty">Insufficient approved graph evidence for a GTM brief.</div> : null}
      {error ? <ErrorState message={error} /> : null}
      <AgentResult result={result} />
    </div>
  );
}

function AgentResult({ result }: { result: GTMAgentResult | null }) {
  if (!result) return null;
  return (
    <div className="agent-grid">
      <section className="panel">
        <h2>Prospecting brief</h2>
        <pre>{JSON.stringify(result, null, 2)}</pre>
      </section>
      <section className="panel">
        <h2>Approved proof points</h2>
        <pre>{JSON.stringify(result.approved_proof_points_used, null, 2)}</pre>
      </section>
      <section className="panel">
        <h2>Graph evidence</h2>
        <pre>{JSON.stringify({ graph_node_slugs: result.graph_node_slugs, source_documents: result.source_documents }, null, 2)}</pre>
      </section>
    </div>
  );
}
