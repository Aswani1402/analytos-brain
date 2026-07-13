# Access Control

Runtime enforcement lives in `apps/api/access_control.py`. The policy artifact
in `policies/analytos.cedar` records the equivalent Cedar-style intent.

Roles:

- `reviewer`: reads review diffs, approves, merges, rejects, deletes ingestion branches.
- `content-agent`: reads `main` Product, Feature, and externally approved ProofPoint only.
- `gtm-agent`: reads `main` Product, Feature, ICPSegment, Persona, and externally approved ProofPoint only.
- `dashboard-reader`: reads approved `main`, cannot write or merge.
- `ingestion-service`: creates/writes ingestion branches, cannot write directly to `main` or approve.

Actors are resolved by prefix: `reviewer-*`, `content-agent*`, `gtm-agent*`,
`dashboard*`, and `ingestion*`.

Tests in `tests/test_agents_access_mcp.py` cover required allow and deny cases.

## Native Omnigraph Policy

`omnigraph/cluster.yaml` references `../policies/analytos.cedar` as a native
cluster policy resource. With Omnigraph 0.8.1, the supported file format is YAML
`PolicyConfig`, not raw Cedar text.

Verified native commands:

```powershell
& "$HOME\.local\bin\omnigraph.exe" cluster validate --config omnigraph
& "$HOME\.local\bin\omnigraph.exe" cluster apply --config omnigraph
& "$HOME\.local\bin\omnigraph.exe" policy validate --cluster omnigraph --graph knowledge
```

Native policy explain results:

- `content-agent` read on `main`: allow
- `gtm-agent` read on `main`: allow
- `dashboard-reader` branch merge: deny
- `ingestion-service` change on `main`: deny

Known limitation: the installed policy engine gates coarse graph and branch
actions. Node-type restrictions such as “content-agent denied EmailThread” are
enforced in the API and MCP filtering layer.
