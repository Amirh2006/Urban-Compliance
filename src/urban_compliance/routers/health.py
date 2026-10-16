"""Health and liveness endpoints."""

from fastapi import APIRouter

from .. import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness probe used by operators and integration tests."""
    return {"status": "ok", "version": __version__}