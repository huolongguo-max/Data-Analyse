from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_DATABASE_PATH = Path(__file__).resolve().parents[1] / "test_app.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DATABASE_PATH.as_posix()}")

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
