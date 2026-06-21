"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import (
    admin,
    analytics,
    applications,
    auth,
    documents,
    jobs,
    outreach,
    profile,
)
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.metrics import PrometheusMiddleware, metrics_endpoint
from app.db.base import Base
from app.db.session import engine

configure_logging()
log = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # dev convenience; prod uses Alembic
    log.info("startup", env=settings.environment, scrapers=settings.enabled_scrapers())
    yield
    log.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Autonomous AI job-search & application platform",
    lifespan=lifespan,
)

app.add_middleware(PrometheusMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    profile.router,
    jobs.router,
    applications.router,
    documents.router,
    outreach.router,
    analytics.router,
    admin.router,
):
    app.include_router(router)

@app.get("/metrics", tags=["health"])
def metrics():
    return metrics_endpoint()


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "version": __version__, "env": settings.environment}


@app.get("/", tags=["health"])
def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs", "health": "/health"}
