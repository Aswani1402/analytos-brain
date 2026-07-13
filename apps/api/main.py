from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import load_api_settings
from .database import init_db
from .routers import changes, entities, health, ingestion, reviews, search
from .services.audit_service import AuditService
from .services.diff_service import DiffService
from .services.ingestion_service import IngestionService
from .services.omnigraph_service import OmnigraphService
from .services.review_service import ReviewService


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = load_api_settings()
        init_db(settings.database_path)
        omnigraph = OmnigraphService(
            settings.omnigraph_bin,
            settings.graph_uri,
            settings.query_file,
            timeout_seconds=settings.command_timeout_seconds,
        )
        audit = AuditService(settings.database_path)
        diff = DiffService(omnigraph)
        ingestion_service = IngestionService(settings, omnigraph, audit)
        review = ReviewService(ingestion_service, omnigraph, diff, audit)
        app.state.settings = settings
        app.state.omnigraph_service = omnigraph
        app.state.audit_service = audit
        app.state.diff_service = diff
        app.state.ingestion_service = ingestion_service
        app.state.review_service = review
        yield

    app = FastAPI(title="Analytos Brain API", version="0.1.0", lifespan=lifespan)

    app.include_router(health.router)
    app.include_router(ingestion.router)
    app.include_router(reviews.router)
    app.include_router(entities.router)
    app.include_router(search.router)
    app.include_router(changes.router)
    return app


app = create_app()
