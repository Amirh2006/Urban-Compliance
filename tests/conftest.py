"""Shared pytest fixtures and environment setup."""

import os
import tempfile
from pathlib import Path

import pytest

# Use a temporary directory for tests so they never touch real data.
_TMP = tempfile.mkdtemp(prefix="uc_test_")
os.environ.setdefault("UC_DATA_DIR", _TMP)
os.environ.setdefault("UC_DATABASE_URL", f"sqlite:///{Path(_TMP) / 'test.db'}")


@pytest.fixture(autouse=True)
def _clean_rules_table():
    """Ensure every test starts with an empty rules table.

    Rules persist across tests within the same SQLite file, so without this
    fixture a rule created in one test can leak into another and change its
    outcome. We also ensure the schema exists before querying.
    """
    from urban_compliance import models  # noqa: F401  (register ORM models)
    from urban_compliance.db import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        session.query(models.Rule).delete()
        session.commit()
    finally:
        session.close()
    yield