"""
Integration tests for the FastAPI backend (Sprint 1).
Uses TestClient (synchronous) and an in-memory SQLite database.
Docling is mocked so tests run without the heavy dependency.
"""
import io
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def mock_parse_result():
    return {
        "pages": [
            {
                "page_number": 1,
                "elements": [
                    {"type": "text", "content": "안녕하세요", "language": "ko"},
                    {"type": "text", "content": "Hello World", "language": "en"},
                ],
            }
        ],
        "metadata": {
            "total_pages": 1,
            "languages": ["ko", "en"],
            "has_tables": False,
            "has_images": False,
        },
    }


@pytest.fixture(scope="module")
def client(tmp_path_factory, mock_parse_result):
    tmp = tmp_path_factory.mktemp("veluga_test")
    db_path = tmp / "test.db"
    upload_dir = tmp / "uploads"
    upload_dir.mkdir()

    import src.backend.config as cfg_module
    cfg_module.DATABASE_URL = f"sqlite:///{db_path}"
    cfg_module.UPLOAD_DIR = upload_dir

    # Patch the database engine to use the test DB
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

    with patch("src.backend.services.parser.parse_pdf", return_value=mock_parse_result):
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestUpload:
    def test_upload_pdf_returns_job_id(self, client):
        pdf_content = b"%PDF-1.4 test content"
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["filename"] == "test.pdf"
        assert data["status"] == "pending"
        assert "created_at" in data

    def test_upload_non_pdf_rejected(self, client):
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", io.BytesIO(b"not a pdf"), "text/plain")},
        )
        assert response.status_code == 400

    def test_upload_pdf_by_extension_accepted(self, client):
        """PDF detected by .pdf extension even with generic content-type."""
        pdf_content = b"%PDF-1.4 test"
        response = client.post(
            "/api/upload",
            files={"file": ("document.pdf", io.BytesIO(pdf_content), "application/octet-stream")},
        )
        assert response.status_code == 200


class TestJobStatus:
    def test_get_nonexistent_job_returns_404(self, client):
        response = client.get("/api/jobs/nonexistent-id")
        assert response.status_code == 404

    def test_upload_then_get_job_status(self, client):
        pdf_content = b"%PDF-1.4 status test"
        upload_resp = client.post(
            "/api/upload",
            files={"file": ("status_test.pdf", io.BytesIO(pdf_content), "application/pdf")},
        )
        assert upload_resp.status_code == 200
        job_id = upload_resp.json()["job_id"]

        # Poll for completion (background task runs synchronously in TestClient)
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] in ("pending", "running", "completed", "failed")

    def test_list_jobs_returns_paginated_result(self, client):
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_jobs_pagination_params(self, client):
        response = client.get("/api/jobs?page=1&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 5
        assert len(data["items"]) <= 5
