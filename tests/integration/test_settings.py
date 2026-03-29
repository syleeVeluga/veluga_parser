"""
Integration tests for settings API (Sprint 2).
Covers GET/POST /api/settings/api-keys.
"""
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("settings_test")
    db_path = tmp / "test.db"
    upload_dir = tmp / "uploads"
    upload_dir.mkdir()

    import src.backend.config as cfg_module
    cfg_module.DATABASE_URL = f"sqlite:///{db_path}"
    cfg_module.UPLOAD_DIR = upload_dir
    cfg_module.GEMINI_API_KEY = ""  # Start unconfigured

    import src.backend.database as db_module
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker

    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(test_engine, "connect")
    def set_wal(conn, _):
        conn.cursor().execute("PRAGMA journal_mode=WAL")

    db_module.engine = test_engine
    db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    from src.backend.main import app
    from src.backend.database import create_tables
    create_tables()

    with TestClient(app) as c:
        yield c


def test_get_api_key_status_unconfigured(client):
    """GET returns gemini_configured=false when key not set."""
    import src.backend.config as cfg
    cfg.GEMINI_API_KEY = ""
    resp = client.get("/api/settings/api-keys")
    assert resp.status_code == 200
    data = resp.json()
    assert "gemini_configured" in data
    assert data["gemini_configured"] is False


def test_get_api_key_never_returns_raw_key(client):
    """GET response must not contain the API key value."""
    import src.backend.config as cfg
    cfg.GEMINI_API_KEY = "super-secret-key-12345"
    resp = client.get("/api/settings/api-keys")
    assert resp.status_code == 200
    body = resp.text
    assert "super-secret-key-12345" not in body
    cfg.GEMINI_API_KEY = ""


def test_post_api_key_updates_configured_status(client, tmp_path):
    """POST sets key; subsequent GET returns gemini_configured=true."""
    import src.backend.config as cfg
    cfg.GEMINI_API_KEY = ""

    with patch("src.backend.routes.settings.set_key") as mock_set_key:
        resp = client.post(
            "/api/settings/api-keys",
            json={"gemini_api_key": "test-gemini-key-abc"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"gemini_configured": True}

    # In-process config should be updated
    assert cfg.GEMINI_API_KEY == "test-gemini-key-abc"

    # Subsequent GET should reflect configured state
    resp2 = client.get("/api/settings/api-keys")
    assert resp2.json()["gemini_configured"] is True


def test_post_empty_key_returns_400(client):
    """POST with empty string key returns HTTP 400."""
    resp = client.post("/api/settings/api-keys", json={"gemini_api_key": ""})
    assert resp.status_code == 400


def test_post_api_key_writes_to_env_file(client, tmp_path):
    """POST calls dotenv set_key with correct arguments."""
    import src.backend.config as cfg
    cfg.GEMINI_API_KEY = ""

    with patch("src.backend.routes.settings.set_key") as mock_set_key:
        resp = client.post(
            "/api/settings/api-keys",
            json={"gemini_api_key": "new-key-xyz"},
        )
    assert resp.status_code == 200
    mock_set_key.assert_called_once()
    call_args = mock_set_key.call_args
    assert call_args[0][1] == "GEMINI_API_KEY"
    assert call_args[0][2] == "new-key-xyz"
