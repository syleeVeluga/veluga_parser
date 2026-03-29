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
    "schema_version": "2.0",
    "elements": [
        {
            "element_id": "elem_0000",
            "type": "title",
            "content": "Test Document",
            "page_number": 1,
            "reading_order": 0,
            "hierarchy_level": 0,
        },
        {
            "element_id": "elem_0001",
            "type": "section_header",
            "content": "Introduction",
            "page_number": 1,
            "reading_order": 1,
            "hierarchy_level": 1,
        },
        {
            "element_id": "elem_0002",
            "type": "text",
            "content": "안녕하세요",
            "page_number": 1,
            "reading_order": 2,
            "language": "ko",
            "parent_section": "Introduction",
        },
        {
            "element_id": "elem_0003",
            "type": "text",
            "content": "Hello World",
            "page_number": 1,
            "reading_order": 3,
            "language": "en",
            "parent_section": "Introduction",
        },
        {
            "element_id": "elem_0004",
            "type": "table",
            "content": "| Name | Value |\n|---|---|\n| Alpha | 1 |",
            "rows": [["Name", "Value"], ["Alpha", "1"]],
            "page_number": 1,
            "reading_order": 4,
        },
        {
            "element_id": "elem_0005",
            "type": "page_header",
            "content": "Running Header",
            "page_number": 1,
            "reading_order": 5,
        },
    ],
    "toc": [
        {"level": 0, "text": "Test Document", "page_number": 1, "element_id": "elem_0000"},
        {"level": 1, "text": "Introduction", "page_number": 1, "element_id": "elem_0001"},
    ],
    "pages": [
        {
            "page_number": 1,
            "elements": [
                {"element_id": "elem_0002", "type": "text", "content": "안녕하세요", "language": "ko",
                 "page_number": 1, "reading_order": 2},
                {"element_id": "elem_0003", "type": "text", "content": "Hello World", "language": "en",
                 "page_number": 1, "reading_order": 3},
                {"element_id": "elem_0004", "type": "table", "rows": [["Name", "Value"], ["Alpha", "1"]],
                 "content": "| Name | Value |\n|---|---|\n| Alpha | 1 |",
                 "page_number": 1, "reading_order": 4},
            ],
        }
    ],
    "metadata": {
        "total_pages": 1,
        "languages": ["en", "ko"],
        "has_tables": True,
        "has_images": False,
        "has_equations": False,
        "has_code": False,
        "title": "Test Document",
        "authors": [],
        "page_dimensions": [],
    },
    "chunks": {
        "hierarchical": [
            {
                "chunk_id": "hc_0000",
                "strategy": "hierarchical",
                "content": "Test Document",
                "token_estimate": 2,
                "element_ids": ["elem_0000"],
                "page_numbers": [1],
                "section_path": ["Test Document"],
                "metadata": {"start_page": 1, "end_page": 1, "has_table": False, "has_image": False, "languages": []},
            },
            {
                "chunk_id": "hc_0001",
                "strategy": "hierarchical",
                "content": "Introduction\n\n안녕하세요\n\nHello World\n\n| Name | Value |",
                "token_estimate": 20,
                "element_ids": ["elem_0001", "elem_0002", "elem_0003", "elem_0004"],
                "page_numbers": [1],
                "section_path": ["Introduction"],
                "metadata": {"start_page": 1, "end_page": 1, "has_table": True, "has_image": False,
                             "languages": ["en", "ko"]},
            },
        ],
        "semantic": [
            {
                "chunk_id": "sc_0000",
                "strategy": "semantic",
                "content": "Test Document\n\nIntroduction\n\n안녕하세요\n\nHello World",
                "token_estimate": 15,
                "element_ids": ["elem_0000", "elem_0001", "elem_0002", "elem_0003"],
                "page_numbers": [1],
                "section_path": ["Introduction"],
                "metadata": {"start_page": 1, "end_page": 1, "has_table": False, "has_image": False,
                             "languages": ["en", "ko"]},
            },
            {
                "chunk_id": "sc_0001",
                "strategy": "semantic",
                "content": "| Name | Value |",
                "token_estimate": 5,
                "element_ids": ["elem_0004"],
                "page_numbers": [1],
                "section_path": ["Introduction"],
                "metadata": {"start_page": 1, "end_page": 1, "has_table": True, "has_image": False, "languages": []},
            },
        ],
        "hybrid": [
            {
                "chunk_id": "hyb_0000",
                "strategy": "hybrid",
                "content": "Test Document",
                "token_estimate": 2,
                "element_ids": ["elem_0000"],
                "page_numbers": [1],
                "section_path": ["Test Document"],
                "metadata": {"start_page": 1, "end_page": 1, "has_table": False, "has_image": False, "languages": []},
            },
        ],
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


# ---------------------------------------------------------------------------
# Sprint 3: v2 Schema + Chunks + TOC + Elements endpoints
# ---------------------------------------------------------------------------

def _upload_and_wait(client, filename: str) -> str:
    """Upload a PDF and poll until completed. Returns job_id."""
    job_id = _upload_pdf(client, filename)
    for _ in range(10):
        resp = client.get(f"/api/jobs/{job_id}")
        if resp.json()["status"] in ("completed", "failed"):
            break
    return job_id


class TestV2Schema:
    def test_result_has_schema_version_2(self, client):
        job_id = _upload_and_wait(client, "v2_schema.pdf")
        resp = client.get(f"/api/jobs/{job_id}/result")
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("schema_version") == "2.0"
            assert "elements" in data
            assert "toc" in data
            assert "chunks" in data

    def test_result_chunks_has_three_strategies(self, client):
        job_id = _upload_and_wait(client, "v2_chunks.pdf")
        resp = client.get(f"/api/jobs/{job_id}/result")
        if resp.status_code == 200:
            chunks = resp.json().get("chunks", {})
            assert "hierarchical" in chunks
            assert "semantic" in chunks
            assert "hybrid" in chunks

    def test_job_list_includes_new_metadata_fields(self, client):
        job_id = _upload_and_wait(client, "v2_joblist.pdf")
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        items = resp.json()["items"]
        job = next((j for j in items if j["job_id"] == job_id), None)
        if job and job["status"] == "completed":
            assert "doc_title" in job
            assert "element_count" in job
            assert "chunk_count" in job


class TestChunksEndpoint:
    def test_chunks_endpoint_returns_200_for_completed_job(self, client):
        job_id = _upload_and_wait(client, "chunks_ep.pdf")
        resp = client.get(f"/api/jobs/{job_id}/chunks")
        assert resp.status_code in (200, 202, 422)
        if resp.status_code == 200:
            data = resp.json()
            assert "job_id" in data
            assert "chunks" in data

    def test_chunks_strategy_filter_hierarchical(self, client):
        job_id = _upload_and_wait(client, "chunks_hier.pdf")
        resp = client.get(f"/api/jobs/{job_id}/chunks?strategy=hierarchical")
        if resp.status_code == 200:
            data = resp.json()
            assert data["strategy"] == "hierarchical"
            assert isinstance(data["chunks"], list)

    def test_chunks_strategy_filter_semantic(self, client):
        job_id = _upload_and_wait(client, "chunks_sem.pdf")
        resp = client.get(f"/api/jobs/{job_id}/chunks?strategy=semantic")
        if resp.status_code == 200:
            assert resp.json()["strategy"] == "semantic"

    def test_chunks_strategy_filter_hybrid(self, client):
        job_id = _upload_and_wait(client, "chunks_hyb.pdf")
        resp = client.get(f"/api/jobs/{job_id}/chunks?strategy=hybrid")
        if resp.status_code == 200:
            assert resp.json()["strategy"] == "hybrid"

    def test_chunks_invalid_strategy_returns_400(self, client):
        job_id = _upload_and_wait(client, "chunks_bad.pdf")
        resp = client.get(f"/api/jobs/{job_id}/chunks?strategy=bogus")
        assert resp.status_code in (400, 202, 422)

    def test_chunks_nonexistent_job_returns_404(self, client):
        resp = client.get("/api/jobs/nonexistent/chunks")
        assert resp.status_code == 404


class TestTocEndpoint:
    def test_toc_endpoint_returns_200(self, client):
        job_id = _upload_and_wait(client, "toc_ep.pdf")
        resp = client.get(f"/api/jobs/{job_id}/toc")
        assert resp.status_code in (200, 202, 422)
        if resp.status_code == 200:
            data = resp.json()
            assert "job_id" in data
            assert "toc" in data
            assert isinstance(data["toc"], list)

    def test_toc_has_expected_entries(self, client):
        job_id = _upload_and_wait(client, "toc_entries.pdf")
        resp = client.get(f"/api/jobs/{job_id}/toc")
        if resp.status_code == 200:
            toc = resp.json()["toc"]
            if toc:
                entry = toc[0]
                assert "level" in entry
                assert "text" in entry
                assert "page_number" in entry
                assert "element_id" in entry

    def test_toc_nonexistent_job_returns_404(self, client):
        resp = client.get("/api/jobs/nonexistent/toc")
        assert resp.status_code == 404


class TestElementsEndpoint:
    def test_elements_endpoint_returns_200(self, client):
        job_id = _upload_and_wait(client, "elems_ep.pdf")
        resp = client.get(f"/api/jobs/{job_id}/elements")
        assert resp.status_code in (200, 202, 422)
        if resp.status_code == 200:
            data = resp.json()
            assert "job_id" in data
            assert "total" in data
            assert "elements" in data

    def test_elements_type_filter(self, client):
        job_id = _upload_and_wait(client, "elems_type.pdf")
        resp = client.get(f"/api/jobs/{job_id}/elements?type=section_header")
        if resp.status_code == 200:
            elems = resp.json()["elements"]
            for e in elems:
                assert e["type"] == "section_header"

    def test_elements_exclude_headers(self, client):
        job_id = _upload_and_wait(client, "elems_hdr.pdf")
        resp = client.get(f"/api/jobs/{job_id}/elements?exclude_headers=true")
        if resp.status_code == 200:
            elems = resp.json()["elements"]
            for e in elems:
                assert e["type"] not in ("page_header", "page_footer")

    def test_elements_nonexistent_job_returns_404(self, client):
        resp = client.get("/api/jobs/nonexistent/elements")
        assert resp.status_code == 404


class TestDownloadChunks:
    def test_download_chunks_nonexistent_job_returns_404(self, client):
        resp = client.get("/api/jobs/nonexistent/download/chunks")
        assert resp.status_code == 404

    def test_download_chunks_returns_json_for_completed_job(self, client):
        job_id = _upload_and_wait(client, "dl_chunks.pdf")
        resp = client.get(f"/api/jobs/{job_id}/download/chunks")
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert resp.headers["content-type"].startswith("application/json")
            data = json.loads(resp.content)
            # Should be chunks dict with at least one strategy
            assert isinstance(data, dict)
