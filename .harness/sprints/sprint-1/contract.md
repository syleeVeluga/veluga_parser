# Sprint 1 Contract: Backend Core — docling Integration + Async Job Processing

## Sprint Goal
A working FastAPI backend that accepts PDF uploads, queues async parsing jobs using docling, and stores results in SQLite.

## Implementation Goals
1. Project scaffold with all dependencies configured
2. SQLAlchemy models for Job and ParsedResult
3. FastAPI app with upload and health endpoints
4. docling-based parser service supporting Korean (EasyOCR pipeline)
5. BackgroundTasks integration for async job lifecycle management
6. File storage structure: `uploads/{job_id}/input.pdf` and `uploads/{job_id}/images/`

## Testable Success Criteria
- [ ] `POST /api/upload` accepts a PDF file and returns `{job_id, filename, status: "pending", created_at}`
- [ ] `GET /api/jobs/{job_id}` returns job metadata with current status
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] Background task transitions job from pending → running → completed (or failed with error_message)
- [ ] `parsed_results` table row exists with `result_json` after successful parse
- [ ] `pytest tests/unit/test_parser.py` passes (mocked docling)
- [ ] `pytest tests/integration/test_api.py` passes (upload + status check)

## Out-of-Scope for This Sprint
- Export format generation (JSON/MD/TXT files) — Sprint 2
- Frontend UI — Sprint 3
- Job listing/pagination — Sprint 2
- Download endpoints — Sprint 2
- DELETE endpoint — Sprint 2

## Technical Decisions
- Use `uuid.uuid4()` for job IDs (string stored in SQLite)
- Store files at `uploads/{job_id}/input.pdf` relative to backend working directory
- Use `python-dotenv` for config; `UPLOAD_DIR` and `DATABASE_URL` from `.env`
- SQLite WAL mode enabled on startup
- docling `DocumentConverter` with EasyOCR pipeline for Korean support
- Internal result schema: `{pages: [{page_number, elements: [{type, content, bbox, language?}]}], metadata: {total_pages, languages, has_tables, has_images}}`
- parser.py detects languages from element content using langdetect or heuristic
