# Agents

## Content Agent

Endpoint:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/agents/content -ContentType "application/json" -Body '{"topic":"reducing manufacturing inventory","actor":"content-agent"}'
```

The agent reads approved `main` only. It requires at least three externally
approved ProofPoint records and returns a title, draft, facts used, graph node
slugs, source documents, and graph evidence.

## GTM Agent

Endpoint:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/agents/gtm -ContentType "application/json" -Body '{"product":"Stockly","actor":"gtm-agent"}'
```

The agent reads approved `main` only. It returns ICP, firmographic, persona,
proof-point, opening-angle, and illustrative-company sections. Illustrative
company examples are clearly marked and are never graph facts.
