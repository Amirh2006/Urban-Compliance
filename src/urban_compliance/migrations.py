"""Idempotent, SQLite-safe schema upgrades.

Alembic is intentionally not used yet; this module handles small additive
changes needed between releases. Every operation must be safe to run on
every startup and must never destroy user data.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _column_exists(conn: Connection, table: str, column: str) -> bool:
    """Return True when ``column`` already exists on ``table`` (SQLite)."""
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def ensure_schema_upgrades() -> None:
    """Apply additive schema changes that ``create_all`` cannot perform."""
    # Imported here to avoid a circular import at module load time.
    from .db import engine

    with engine.begin() as conn:
        # Phase 1.3: spatial scope on projects.
        if not _column_exists(conn, "projects", "spatial_scope"):
            conn.execute(
                text("ALTER TABLE projects ADD COLUMN spatial_scope VARCHAR(120)")
            )