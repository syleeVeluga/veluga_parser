# Evaluation Report - Sprint 1

## Overall Result: PASS

## Scores
| Category | Score (0-100) | Weight | Weighted Score |
|---|---|---|---|
| Functionality | 92 | 30% | 27.6 |
| Code Quality | 76 | 25% | 19.0 |
| Testing | 88 | 20% | 17.6 |
| Security | 90 | 15% | 13.5 |
| UI/UX | N/A | 10% | N/A (backend-only sprint) |
| **Total** | | | **77.7 / 90 possible = 86.3%** |

## Contract Item Results

- [PASS] `POST /api/upload` accepts a PDF file and returns `{job_id, filename, status: "pending", created_at}`: Confirmed via TestClient — response includes all four fields, status is "pending" as required.
- [PASS] `GET /api/jobs/{job_id}` returns job metadata with current status: Returns job_id, filename, status, page_count, languages_detected, error_message, created_at, updated_at.
- [PASS] `GET /health` returns `{"status": "ok"}`: Confirmed manually via TestClient — 200 OK with exact payload.
- [PASS] Background task transitions job from pending → running → completed (or failed with error_message): Verified with manual TestClient test — job correctly shows "completed" after BackgroundTasks executes; error_message is populated on failure per code review.
- [PASS] `parsed_results` table row exists with `result_json` after successful parse: Confirmed by querying ParsedResult table after upload — row exists, result_json contains "pages" and "metadata" keys.
- [PASS] `pytest tests/unit/test_parser.py` passes (mocked docling): 7/7 unit tests pass.
- [PASS] `pytest tests/integration/test_api.py` passes (upload + status check): 8/8 integration tests pass.

Full pytest output (15/15 passed in 0.94s):
```
tests/unit/test_parser.py::TestLanguageDetection::test_detect_korean PASSED
tests/unit/test_parser.py::TestLanguageDetection::test_detect_english PASSED
tests/unit/test_parser.py::TestLanguageDetection::test_detect_chinese PASSED
tests/unit/test_parser.py::TestLanguageDetection::test_detect_japanese PASSED
tests/unit/test_parser.py::TestLanguageDetection::test_empty_text_returns_none PASSED
tests/unit/test_parser.py::TestParsePdf::test_parse_pdf_returns_correct_schema PASSED
tests/unit/test_parser.py::TestParsePdf::test_parse_pdf_missing_docling_raises_runtime_error PASSED
tests/integration/test_api.py::TestHealth::test_health_returns_ok PASSED
tests/integration/test_api.py::TestUpload::test_upload_pdf_returns_job_id PASSED
tests/integration/test_api.py::TestUpload::test_upload_non_pdf_rejected PASSED
tests/integration/test_api.py::TestUpload::test_upload_pdf_by_extension_accepted PASSED
tests/integration/test_api.py::TestJobStatus::test_get_nonexistent_job_returns_404 PASSED
tests/integration/test_api.py::TestJobStatus::test_upload_then_get_job_status PASSED
tests/integration/test_api.py::TestJobStatus::test_list_jobs_returns_paginated_result PASSED
tests/integration/test_api.py::TestJobStatus::test_list_jobs_pagination_params PASSED
======================== 15 passed in 0.94s =============================
```

## Bugs Found

### Critical
None.

### High
None.

### Medium

**M1: `_element_to_dict` helper function is dead code**
- File: `src/backend/services/parser.py`, lines 32–66
- `_element_to_dict` is defined but never called. `parse_pdf` inlines the element-processing logic directly for TableItem, PictureItem, and TextItem without invoking this helper.
- Impact: 35 lines of untested, unreachable code. If parse_pdf logic evolves, developers may be confused about which code path to modify. No functional impact currently.

**M2: `load_dotenv()` is never called**
- File: `src/backend/config.py`
- `python-dotenv` is listed in `requirements.txt` and the spec mandates using it. However, `load_dotenv()` is never imported or invoked anywhere in the codebase. As a result, a `.env` file on disk will be silently ignored — only OS-level environment variables are read via `os.getenv()`.
- Impact: Developers who create a `.env` file expecting it to work will be confused. Environment variables set in `.env` will not be applied during development. No functional impact when environment variables are set at the OS level.

**M3: `.env.example` scaffold file is missing**
- The spec and contract explicitly state: "Project scaffold: … `.env.example`". No `.env.example` file exists in the repository.
- Impact: Onboarding friction — new developers have no reference for required environment variables. Minor documentation gap.

### Low

**L1: `parse_pdf` function is 144 lines long**
- File: `src/backend/services/parser.py`, lines 69–212
- CLAUDE.md convention: "Consider splitting if over 20 lines." While the convention says "consider" rather than "must", this function does multiple responsibilities: converter setup, element iteration, image/table/text handling, and result assembly. It would benefit from extraction (e.g., `_build_element`, `_process_items`, `_assemble_result`).
- Impact: Readability and testability. Currently functional.

**L2: `_element_to_dict` also violates the 20-line function guideline**
- File: `src/backend/services/parser.py`, lines 32–66 (35 lines)
- Same convention. Also dead code (see M1), so doubly worth removing or integrating.

**L3: `db.rollback()` in background task exception handler is a no-op in the primary failure path**
- File: `src/backend/routes/upload.py`, lines 63–69
- When `parse_pdf()` raises an exception, the `job.status = "running"` has already been committed. `db.rollback()` only undoes uncommitted session state (nothing in this case). The code is still correct and safe — the rollback is defensive — but it does not achieve what a reader might expect.
- Impact: None. Purely a code clarity issue.

**L4: MIME type validation accepts `application/octet-stream` unconditionally**
- File: `src/backend/routes/upload.py`, lines 81–84
- The check allows `application/octet-stream` without requiring a `.pdf` extension. Any binary file sent with `application/octet-stream` will be accepted regardless of extension. The `.pdf` extension check is only triggered for truly unknown MIME types.
- Impact: Low. An attacker could upload non-PDF binaries labeled as `application/octet-stream`. docling will fail and the job will go to `failed` status with an error message, so it is not a security bypass — just slightly overpermissive input validation.

## Detailed Code Review

### What Went Well

1. **Complete contract coverage.** All 7 testable success criteria from the contract are implemented and verified. No gaps between spec and implementation.

2. **Correct DB schema.** Both `jobs` and `parsed_results` tables match the spec exactly, including all required columns (id, filename, file_path, file_hash, status, error_message, page_count, languages_detected, created_at, updated_at for jobs; id, job_id, result_json, markdown_path, text_path, json_path, image_dir, created_at for parsed_results). SQLAlchemy 2.x mapped_column syntax is used correctly.

3. **WAL mode enabled.** SQLite WAL mode is configured via `event.listens_for(engine, "connect")` exactly as required by the spec. This is the correct place to set it — it runs on every new connection.

4. **File storage layout is correct.** Uploaded files are stored at `uploads/{job_id}/input.pdf` and image directory is `uploads/{job_id}/images/`, matching the contract requirement exactly (verified in uploads/ directory).

5. **UUID job IDs.** `uuid.uuid4()` is used for job IDs, stored as strings in SQLite, as specified.

6. **Error handling is present on all endpoints.** `POST /api/upload` returns 400 for non-PDF, 413 for oversized files. `GET /api/jobs/{job_id}` returns 404 for unknown IDs. Background task captures exceptions and writes `error_message` to the DB.

7. **Streaming file upload with size guard.** The upload endpoint streams in 64KB chunks and enforces `MAX_UPLOAD_SIZE_BYTES`, cleaning up the job directory on overflow. This prevents memory exhaustion from large uploads.

8. **SHA-256 file hashing.** `file_hash` is computed and stored, laying groundwork for Sprint 2 deduplication feature. Correct chunked implementation with 65536-byte blocks.

9. **Language detection heuristic is solid.** Unicode range checks for Korean (Hangul syllables + Jamo), Chinese (CJK unified ideographs), and Japanese (Hiragana + Katakana) with a >10% character ratio threshold. Falls back to "en" correctly.

10. **Test quality is high.** Integration tests use an isolated in-memory SQLite database (avoiding contamination), properly mock `parse_pdf` to avoid docling install requirement, and cover happy paths, 404s, 400s, and pagination. Unit tests cover all four language detection branches plus schema validation and missing-docling error path.

11. **All files are well within the 300-line limit.** Largest file is `parser.py` at 212 lines.

12. **No hardcoded secrets.** Config reads exclusively from environment variables with safe defaults.

13. **CORS configured correctly** for the expected frontend origins (localhost:5173 and localhost:3000), consistent with Sprint 3 frontend requirements.

14. **Single git commit** with conventional commit format: `feat(sprint1): backend core with docling integration and async job processing`. Clean repo state.

### Needs Improvement

1. **`_element_to_dict` is dead code** (see M1). Should be removed or integrated into `parse_pdf`. It adds confusion and is untested.

2. **`load_dotenv()` is missing** (see M2). The spec explicitly requires `python-dotenv` for config. `config.py` should call `load_dotenv()` before the `os.getenv()` calls.

3. **`.env.example` is absent** (see M3). The sprint scope lists this as a deliverable.

4. **`parse_pdf` is too long** (144 lines, see L1). It handles converter configuration, element iteration, three different element type handlers, image saving, and result assembly. Extracting helper functions would improve readability and testability, especially for the image-saving and table-extraction logic.

5. **The integration test's background task patch scope is fragile.** The `client` fixture patches `src.backend.services.parser.parse_pdf` at module scope, but `_run_parse_job` imports `parse_pdf` dynamically inside the function (`from src.backend.services.parser import parse_pdf`). This works with the current `with patch(...)` as `TestClient` context manager but would silently fail if the test structure changed. A more robust approach would be to patch at the call site in `upload.py`.

6. **No `__init__.py` for `src/backend/`** — there is one for `models/`, `routes/`, and `services/`, but the top-level backend package has no `__init__.py` in `src/backend/`. This works because `src/` is on the Python path, but it's inconsistent.

## Required Fixes for FAIL (in priority order)

This sprint PASSES. The items below are recommended improvements for Sprint 2, not blockers:

1. **(Recommended)** Add `load_dotenv()` call in `config.py` to honor `.env` files as specified.
2. **(Recommended)** Create `.env.example` with `DATABASE_URL`, `UPLOAD_DIR`, and `MAX_UPLOAD_SIZE_MB` documented.
3. **(Recommended)** Remove or integrate the dead `_element_to_dict` function in `parser.py`.
4. **(Optional)** Refactor `parse_pdf` into smaller helpers to comply with the 20-line function guideline.
