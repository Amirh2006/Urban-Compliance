"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import __version__
from .config import settings
from .db import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create local directories and database tables on startup."""
    settings.ensure_dirs()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Preliminary parcel compliance checks against municipal regulations. "
        "This tool is a decision aid and does not issue official approvals."
    ),
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
def health() -> dict:
    """Liveness probe used by operators and integration tests."""
    return {"status": "ok", "version": __version__}