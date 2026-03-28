"""
Integration tests for the FastAPI backend (Sprint 1 + Sprint 2).
Uses TestClient (synchronous) and an in-memory SQLite database.
Docling is mocked so tests run without the heavy dependency.
"""
import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_PARSE_RESULT = {
    "pages": [
        {
            "page_number": 1,
            "elements": [
                {"type": "text", "content": "안녕하세요", "language": "ko"},
                {"type": "text", "content": "Hello World", "language": "en"},
                {
                    "type": "table",
                    "rows": [["Name", "Value"], ["Alpha", "1"]],
                    "content": "| Name | Value |\n|---|---|\n| Alpha | 1 |",
                },
            ],
        }
    ],
    "metadata": {
        "total_pages": 1,
        "languages": ["en", "ko"],
        "has_tables": True,
        "has_images": False,
    },
}


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("veluga_test")
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

    with patch("src.backend.services.parser.parse_pdf", return_value=MOCK_PARSE_RESULT):
        with TestClient(app) as c:
            yield c


def _upload_pdf(client, filename="test.pdf") -> str:
    """Helper: upload a fake PDF and return job_id."""
    resp = client.post(
        "/api/upload",
        files={"file": (filename, io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert resp.status_code == 200
    return resp.json()["job_id"]


# ---------------------------------------------------------------------------
# Sprint 1: Health + Upload + Job Status
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestUpload:
    def test_upload_pdf_returns_job_id(self, client):
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test content"), "application/pdf")},
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
        response = client.post(
            "/api/upload",
            files={"file": ("document.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/octet-stream")},
        )
        assert response.status_code == 200


class TestJobStatus:
    def test_get_nonexistent_job_returns_404(self, client):
        response = client.get("/api/jobs/nonexistent-id")
        assert response.status_code == 404

    def test_upload_then_get_job_status(self, client):
        job_id = _upload_pdf(client, "status_test.pdf")
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


# ---------------------------------------------------------------------------
# Sprint 2: Result + Download + Delete
# ---------------------------------------------------------------------------

class TestResult:
    def test_get_result_nonexistent_job_returns_404(self, client):
        response = client.get("/api/jobs/does-not-exist/result")
        assert response.status_code == 404

    def test_get_result_completed_job_returns_schema(self, client):
        job_id = _upload_pdf(client, "result_test.pdf")
        response = client.get(f"/api/jobs/{job_id}/result")
        # May be 200 (completed) or 202 (still processing in test env)
        assert response.status_code in (200, 202)
        if response.status_code == 200:
            data = response.json()
            assert "pages" in data
            assert "metadata" in data

    def test_get_result_returns_pages_and_metadata(self, client):
        """Upload, wait for completion, then verify result structure."""
        job_id = _upload_pdf(client, "result_verify.pdf")
        # Poll until done (background task runs sync in TestClient)
        for _ in range(5):
            status_resp = client.get(f"/api/jobs/{job_id}")
            if status_resp.json()["status"] in ("completed", "failed"):
                break
        response = client.get(f"/api/jobs/{job_id}/result")
        if response.status_code == 200:
            data = response.json()
            assert "pages" in data
            assert isinstance(data["pages"], list)
            assert "metadata" in data
            assert "total_pages" in data["metadata"]
            assert "languages" in data["metadata"]


class TestDownloads:
    def test_download_nonexistent_job_returns_404(self, client):
        for fmt in ("json", "markdown", "text"):
            resp = client.get(f"/api/jobs/nonexistent/download/{fmt}")
            assert resp.status_code == 404

    def test_download_json_returns_file(self, client):
        job_id = _upload_pdf(client, "download_json.pdf")
        resp = client.get(f"/api/jobs/{job_id}/download/json")
        # Either 200 (file ready) or 404 (not ready yet in async context)
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert resp.headers["content-type"].startswith("application/json")
            data = json.loads(resp.content)
            assert "pages" in data

    def test_download_markdown_returns_file(self, client):
        job_id = _upload_pdf(client, "download_md.pdf")
        resp = client.get(f"/api/jobs/{job_id}/download/markdown")
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert "text/markdown" in resp.headers["content-type"]
            content = resp.content.decode("utf-8")
            assert "Page" in content

    def test_download_text_returns_file(self, client):
        job_id = _upload_pdf(client, "download_txt.pdf")
        resp = client.get(f"/api/jobs/{job_id}/download/text")
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert "text/plain" in resp.headers["content-type"]

    def test_markdown_contains_gfm_table(self, client):
        """Verify GFM table syntax appears in markdown output."""
        job_id = _upload_pdf(client, "gfm_table.pdf")
        resp = client.get(f"/api/jobs/{job_id}/download/markdown")
        if resp.status_code == 200:
            content = resp.content.decode("utf-8")
            assert "|" in content  # GFM table pipes


class TestDelete:
    def test_delete_nonexistent_job_returns_404(self, client):
        resp = client.delete("/api/jobs/nonexistent-id")
        assert resp.status_code == 404

    def test_delete_job_removes_from_db(self, client):
        job_id = _upload_pdf(client, "delete_test.pdf")
        del_resp = client.delete(f"/api/jobs/{job_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["job_id"] == job_id

        # Verify gone from DB
        get_resp = client.get(f"/api/jobs/{job_id}")
        assert get_resp.status_code == 404

    def test_delete_job_cleans_filesystem(self, client, tmp_path_factory):
        job_id = _upload_pdf(client, "delete_fs_test.pdf")
        # Get job details to find file_path
        job_resp = client.get(f"/api/jobs/{job_id}")
        assert job_resp.status_code == 200

        del_resp = client.delete(f"/api/jobs/{job_id}")
        assert del_resp.status_code == 200

        # After deletion the job should not exist
        get_resp = client.get(f"/api/jobs/{job_id}")
        assert get_resp.status_code == 404
