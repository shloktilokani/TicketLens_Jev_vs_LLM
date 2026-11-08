"""TicketLens API entry point.

Starts without provider keys, and without MongoDB (readiness then reports it unavailable).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure, PyMongoError

from app.api import (
    app_settings,
    bulk_jobs,
    dashboard,
    evaluation,
    executions,
    health,
    imports,
    providers,
    runs,
    taxonomy,
    tickets,
)
from app.core.settings import Settings, get_settings
from app.jobs.bulk import mark_interrupted
from app.repositories.database import DB_UNAVAILABLE_MESSAGE, connect, ensure_indexes
from app.services.app_settings import load_taxonomy

log = logging.getLogger("ticketlens")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logging.basicConfig(level=settings.log_level)
        client = connect(settings)
        app.state.settings = settings
        app.state.mongo = client
        app.state.db = client[settings.mongodb_database]
        try:
            ensure_indexes(app.state.db)
            mark_interrupted(app.state.db)
            load_taxonomy(app.state.db)
        except PyMongoError:
            log.warning("Indexes not created. %s", DB_UNAVAILABLE_MESSAGE)
        yield
        client.close()

    # Interactive API docs are for local development; production does not advertise its API.
    docs = {"docs_url": None, "redoc_url": None, "openapi_url": None}
    extra = docs if settings.app_env == "production" else {}
    app = FastAPI(title="TicketLens API", version="0.1.0", lifespan=lifespan, **extra)
    # Only the local frontend may call the API from a browser (architecture.md section 9).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health.router)
    app.include_router(providers.router)
    app.include_router(taxonomy.router)
    app.include_router(tickets.router)
    app.include_router(imports.router)
    app.include_router(runs.router)
    app.include_router(dashboard.router)
    app.include_router(executions.router)
    app.include_router(bulk_jobs.router)
    app.include_router(evaluation.router)
    app.include_router(app_settings.router)

    @app.exception_handler(ConnectionFailure)
    async def database_unavailable(request: Request, exc: ConnectionFailure) -> JSONResponse:
        log.warning("Database unavailable during %s %s", request.method, request.url.path)
        return JSONResponse(status_code=503, content={"detail": DB_UNAVAILABLE_MESSAGE})

    return app


app = create_app()
