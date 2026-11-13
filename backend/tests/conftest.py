"""Test bootstrap: isolate the database BEFORE the app engine is created.

Every test session gets its own throwaway SQLite file, so tests are
repeatable and never touch dev data.
"""

from __future__ import annotations

import os
import tempfile

# Must happen before `app` (and its engine) is imported anywhere.
_TMP_DIR = tempfile.mkdtemp(prefix="awa-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DIR}/test.db"
os.environ.setdefault("APP_ENV", "development")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c

