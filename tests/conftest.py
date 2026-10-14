"""Shared pytest fixtures and environment setup."""

import os
import tempfile
from pathlib import Path

# Use a temporary directory for tests so they never touch real data.
_TMP = tempfile.mkdtemp(prefix="uc_test_")
os.environ.setdefault("UC_DATA_DIR", _TMP)
os.environ.setdefault("UC_DATABASE_URL", f"sqlite:///{Path(_TMP) / 'test.db'}")