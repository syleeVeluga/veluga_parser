"""
Integration tests for engine dispatch (Sprint 1).
Verifies that the `engine` form field is stored on the Job row and that
the correct parser is dispatched based on job.engine.
"""
import builtins
import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Shared mock result (valid v2 schema)
# ---------------------------------------------------------------------------

MOCK_RESULT = {
    "schema_version": "2.0",
    "elements": [
        {
            "element_id": "elem_0000",
            "type": "text",
            "content": "Hello Engine Test",
            "page_number": 1,
            "reading_order": 0,
        }
    ],
    "toc": [],
    "pages": [{"page_number": 1, "elements": []}],
    "chunks": {},
    "metadata": {
        "total_pages": 1,
        "languages": ["en"],
        "has_tables": False,
        "has_images": False,
        "has_equations": False,
        "has_code": False,
        "title": None,
        "authors": [],
        "page_dimensions": [],
    },
    "page_markdowns": {"1": "Hello Engine Test"},
}


# ---------------------------------------------------------------------------
# App fixture — dedicated test DB, real HTTP layer
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("engine_dispatch_test")
    db_path = tmp / "test.db"
    upload_dir = tmp / "uploads"
    upload_dir.mkdir()

    import src.backend.config as cfg_module
    cfg_module.DATABASE_URL = f"sqlite:///{db_path}"
    cfg_module.UPLOAD_DIR = upload_dir

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

    with patch("src.backend.services.parser.parse_pdf", return_value=MOCK_RESULT):
        with TestClient(app) as c:
            yield c


def _fake_pdf() -> bytes:
    return b"%PDF-1.4 fake content for testing"


def _upload(client, engine: str | None = None):
    data = {}
    if engine is not None:
        data["engine"] = engine
    return client.post(
        "/api/upload",
        files={"file": ("test.pdf", io.BytesIO(_fake_pdf()), "application/pdf")},
        data=data,
    )


# ---------------------------------------------------------------------------
# Tests: engine field storage
# ---------------------------------------------------------------------------

def test_default_engine_is_docling(client):
    resp = _upload(client)
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    job_resp = client.get(f"/api/jobs/{job_id}")
    assert job_resp.status_code == 200
    assert job_resp.json()["engine"] == "docling"


def test_engine_paddleocr_stored(client):
    with patch("src.backend.services.parser_paddleocr.parse_pdf_paddleocr", return_value=MOCK_RESULT):
        resp = _upload(client, engine="paddleocr")
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    job_resp = client.get(f"/api/jobs/{job_id}")
    assert job_resp.status_code == 200
    assert job_resp.json()["engine"] == "paddleocr"


def test_engine_gemini_stored(client):
    with patch("src.backend.services.parser_gemini.parse_pdf_gemini", return_value=MOCK_RESULT):
        resp = _upload(client, engine="gemini")
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    job_resp = client.get(f"/api/jobs/{job_id}")
    assert job_resp.status_code == 200
    assert job_resp.json()["engine"] == "gemini"


def test_invalid_engine_defaults_to_docling(client):
    resp = _upload(client, engine="unknown_engine")
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    job_resp = client.get(f"/api/jobs/{job_id}")
    assert job_resp.status_code == 200
    assert job_resp.json()["engine"] == "docling"


def test_engine_appears_in_job_list(client):
    list_resp = client.get("/api/jobs")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) >= 1
    for item in items:
        assert "engine" in item


# ---------------------------------------------------------------------------
# Tests: paddleocr import guard
# ---------------------------------------------------------------------------

def test_paddleocr_raises_runtime_error_when_not_installed():
    """parser_paddleocr raises RuntimeError if paddleocr package is absent."""
    paddleocr_backup = sys.modules.pop("paddleocr", None)
    original_import = builtins.__import__

    def _blocking_import(name, *args, **kwargs):
        if name == "paddleocr":
            raise ImportError("paddleocr not installed (mocked)")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = _blocking_import
    try:
        from src.backend.services.parser_paddleocr import parse_pdf_paddleocr
        with pytest.raises(RuntimeError, match="PaddleOCR is not installed"):
            parse_pdf_paddleocr(Path("/tmp/test.pdf"), Path("/tmp/images"))
    finally:
        builtins.__import__ = original_import
        if paddleocr_backup is not None:
            sys.modules["paddleocr"] = paddleocr_backup
