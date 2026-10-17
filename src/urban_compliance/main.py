"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import __version__
from .config import settings
from .db import Base, engine
from .routers import analyses, files, health, parcels, projects, reports


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

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(files.router)
app.include_router(parcels.router)
app.include_router(analyses.router)
app.include_router(reports.router)