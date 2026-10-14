"""FastAPI application entry point."""

from fastapi import FastAPI

from . import __version__

app = FastAPI(
    title="Urban Compliance AI",
    version=__version__,
    description=(
        "Preliminary parcel compliance checks against municipal regulations. "
        "This tool is a decision aid and does not issue official approvals."
    ),
)


@app.get("/health", tags=["health"])
def health() -> dict:
    """Liveness probe used by operators and integration tests."""
    return {"status": "ok", "version": __version__}