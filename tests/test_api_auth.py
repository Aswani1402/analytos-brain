from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers import ingestion, reviews


def test_protected_write_routes_require_api_token(monkeypatch):
    monkeypatch.setenv("ANALYTOS_API_TOKEN", "secret")
    app = FastAPI()
    app.include_router(ingestion.router)
    app.include_router(reviews.router)
    client = TestClient(app, raise_server_exceptions=False)
    assert client.post("/ingestions", json={"source_path": "seed-data/x.md", "actor": "ingestion-service"}).status_code == 401
    assert client.get("/reviews/run-1").status_code == 401
    headers = {"Authorization": "Bearer secret"}
    assert client.post("/ingestions", json={"source_path": "seed-data/x.md", "actor": "ingestion-service"}, headers=headers).status_code != 401
