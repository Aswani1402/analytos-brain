Analytos Brain Dashboard
========================

The dashboard is a React, TypeScript, and Vite client for the FastAPI backend. It reads approved knowledge from Omnigraph through the API and stores no graph knowledge in browser storage or frontend source files.

Prerequisites
-------------

- FastAPI backend available at `http://127.0.0.1:8000`
- Node.js and npm
- Omnigraph configured for the backend

Install
-------

```powershell
Set-Location apps\dashboard
npm install
```

Environment
-----------

Create a local frontend `.env` only when overriding the API URL:

```powershell
VITE_API_BASE_URL=http://127.0.0.1:8000
```

`apps/dashboard/.env` is ignored by Git. `apps/dashboard/.env.example` contains the portable default. Hosted environments should set `VITE_API_BASE_URL` to the deployed API origin during build.

Startup
-------

Start the API:

```powershell
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

Start the dashboard:

```powershell
Set-Location apps\dashboard
npm run dev -- --host 127.0.0.1
```

Build
-----

```powershell
Set-Location apps\dashboard
npm run build
```

Routes
------

- `/` overview, health, review counts, ingestion form, recent workflow actions
- `/entities` approved entity browser
- `/products` approved product list
- `/products/:slug` approved product detail with partial relationship support
- `/search` approved-main search
- `/reviews` pending ingestion reviews
- `/reviews/:runId` review diff and approve/reject actions
- `/changes` recent workflow and Omnigraph commit data
- `/agents/content` Content Agent placeholder wired to `POST /agents/content`
- `/agents/gtm` GTM Agent placeholder wired to `POST /agents/gtm`

Ingestion Workflow
------------------

The overview page posts to `POST /ingestions` with `source_path`, `actor`, and `extraction_provider`. It includes quick-select buttons for the five seed file paths but does not embed seed file contents. Successful ingestion returns a run ID, document hash, branch name, status, and review link. The created knowledge remains pending in an ingestion branch until approved.

Review Workflow
---------------

The reviews page reads `GET /reviews`. The review detail page reads `GET /reviews/{run_id}` and displays added, changed, and removed nodes and edges separately. Internal Omnigraph `id` fields are hidden. Counts by node and edge type are displayed when returned by the backend.

Approve and Reject
------------------

Approval posts to `POST /reviews/{run_id}/approve` with a reviewer actor and asks for confirmation before merging the branch into main. Rejection posts to `POST /reviews/{run_id}/reject` with reviewer actor and a non-empty reason, then disables further decision actions once the status changes.

Entity Browser and Search
-------------------------

Entity and product pages call the backend entity endpoints and read approved main only. Search calls `GET /search?q=<text>` and does not search browser-local data.

Recent Changes
--------------

The recent changes page calls `GET /changes/recent` and displays workflow audit actions plus any Omnigraph commit information returned by the backend.

Agent Pages
-----------

The Content Agent and GTM Agent pages are present for assignment navigation. They call `POST /agents/content` and `POST /agents/gtm` when available and show a clear not-yet-implemented state when the backend returns 404. The frontend does not fabricate agent results.

CORS
----

The FastAPI backend allows development dashboard origins from `ANALYTOS_CORS_ORIGINS`, defaulting to `http://localhost:5173,http://127.0.0.1:5173`. Production origins should be configured through that environment variable.
