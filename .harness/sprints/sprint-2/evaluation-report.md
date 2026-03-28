# Evaluation Report - Sprint 2

## Overall Result: PASS

## Scores
| Category | Score (0-100) | Weight | Weighted Score |
|----------|--------------|--------|---------------|
| Functionality | 92 | 30% | 27.6 |
| Code Quality | 85 | 25% | 21.25 |
| Testing | 72 | 20% | 14.4 |
| Security | 80 | 15% | 12.0 |
| UI/UX | N/A | 10% | N/A (backend-only sprint) |
| **Total** | | | **75.25 / 90 weighted pts → ~84%** |

> UI/UX weight (10%) redistributed equally across remaining four categories.
> Adjusted total: Functionality 33.3%, Code Quality 27.8%, Testing 22.2%, Security 16.7% → **84%**

## Contract Item Results

- [PASS] `GET /api/jobs` returns `{total, page, limit, items}` with correct counts: `routes/jobs.py` line 44 returns exactly the required shape. Uses `func.count(Job.id)` for accurate total. Pagination params validated (page >= 1, 1 <= limit <= 100). Integration test `test_list_jobs_returns_paginated_result` and `test_list_jobs_pagination_params` confirmed passing.

- [PASS] `GET /api/jobs/{job_id}/result` returns the internal result schema JSON: `routes/results.py` lines 35–52 return `json.loads(parsed.result_json)` for completed jobs, 202 for pending/running, 422 for failed, 404 for missing. Result structure contains `pages` + `metadata`. Test `test_get_result_returns_pages_and_metadata` confirmed passing.

- [PASS] `GET /api/jobs/{job_id}/download/json` returns JSON file (Content-Disposition: attachment): `routes/results.py` lines 55–67 use `FileResponse(path=..., media_type="application/json", filename=f"{job_id}_result.json")`. FastAPI sets `Content-Disposition: attachment` when `filename` is provided. Confirmed in test `test_download_json_returns_file`.

- [PASS] `GET /api/jobs/{job_id}/download/markdown` returns .md file: `routes/results.py` lines 70–82, `media_type="text/markdown"`, `filename=f"{job_id}_result.md"`. Test confirmed passing.

- [PASS] `GET /api/jobs/{job_id}/download/text` returns .txt file: `routes/results.py` lines 85–97, `media_type="text/plain"`, `filename=f"{job_id}_result.txt"`. Test confirmed passing.

- [PASS] Markdown output uses GFM table syntax for PDFs containing tables: `services/exporter.py` `_table_rows_to_gfm()` generates `| col | col |\n| --- | --- |\n| val | val |` format. Valid GFM (spaces around `---` are permitted by spec). Unit test `test_contains_gfm_table` confirmed passing. Integration test `test_markdown_contains_gfm_table` confirmed passing.

- [PASS] `DELETE /api/jobs/{job_id}` removes DB rows AND `uploads/{job_id}/` directory: `routes/results.py` lines 100–117. Path derivation: `Path(job.file_path).parent` correctly resolves `uploads/{job_id}/` directory. `shutil.rmtree` removes it. `ParsedResult` row deleted before `Job` row (correct FK ordering). Tests `test_delete_job_removes_from_db` and `test_delete_job_cleans_filesystem` confirmed passing.

- [PASS] All three download endpoints return 404 for non-existent jobs: `_get_job_or_404` helper raises `HTTPException(404, "Job not found")`. Test `test_download_nonexistent_job_returns_404` iterates all three formats and confirms 404.

- [PASS] All three download endpoints return 404 if result not ready (pending/running): `if job.status != "completed": raise HTTPException(status_code=404, detail="Result not ready")`. Covers pending, running, and also failed status (reasonable extension of the contract).

- [PASS] `pytest tests/integration/test_api.py` covers all new endpoints: 19 integration tests cover health, upload, job status, list, result, all three downloads (including GFM check), and delete (two scenarios). All 42 total tests pass in 1.50s.

## Test Run Output (verbatim)

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: D:\dev\veluga_parser
configfile: pytest.ini
plugins: anyio-4.12.1, Faker-40.4.0, asyncio-1.3.0
asyncio: mode=Mode.AUTO, debug=False
collected 42 items

tests/integration/test_api.py::TestHealth::test_health_returns_ok PASSED [  2%]
tests/integration/test_api.py::TestUpload::test_upload_pdf_returns_job_id PASSED [  4%]
tests/integration/test_api.py::TestUpload::test_upload_non_pdf_rejected PASSED [  7%]
tests/integration/test_api.py::TestUpload::test_upload_pdf_by_extension_accepted PASSED [  9%]
tests/integration/test_api.py::TestJobStatus::test_get_nonexistent_job_returns_404 PASSED [ 11%]
tests/integration/test_api.py::TestJobStatus::test_upload_then_get_job_status PASSED [ 14%]
tests/integration/test_api.py::TestJobStatus::test_list_jobs_returns_paginated_result PASSED [ 16%]
tests/integration/test_api.py::TestJobStatus::test_list_jobs_pagination_params PASSED [ 19%]
tests/integration/test_api.py::TestResult::test_get_result_nonexistent_job_returns_404 PASSED [ 21%]
tests/integration/test_api.py::TestResult::test_get_result_completed_job_returns_schema PASSED [ 23%]
tests/integration/test_api.py::TestResult::test_get_result_returns_pages_and_metadata PASSED [ 26%]
tests/integration/test_api.py::TestDownloads::test_download_nonexistent_job_returns_404 PASSED [ 28%]
tests/integration/test_api.py::TestDownloads::test_download_json_returns_file PASSED [ 30%]
tests/integration/test_api.py::TestDownloads::test_download_markdown_returns_file PASSED [ 33%]
tests/integration/test_api.py::TestDownloads::test_download_text_returns_file PASSED [ 35%]
tests/integration/test_api.py::TestDownloads::test_markdown_contains_gfm_table PASSED [ 38%]
tests/integration/test_api.py::TestDelete::test_delete_nonexistent_job_returns_404 PASSED [ 40%]
tests/integration/test_api.py::TestDelete::test_delete_job_removes_from_db PASSED [ 42%]
tests/integration/test_api.py::TestDelete::test_delete_job_cleans_filesystem PASSED [ 45%]
tests/unit/test_exporter.py::TestToJson::test_creates_valid_json_file PASSED [ 47%]
tests/unit/test_exporter.py::TestToJson::test_preserves_unicode PASSED   [ 50%]
tests/unit/test_exporter.py::TestToJson::test_creates_parent_dirs PASSED [ 52%]
tests/unit/test_exporter.py::TestTableToGfm::test_single_row_is_header_only PASSED [ 54%]
tests/unit/test_exporter.py::TestTableToGfm::test_two_rows_header_and_data PASSED [ 57%]
tests/unit/test_exporter.py::TestTableToGfm::test_empty_rows_returns_empty PASSED [ 59%]
tests/unit/test_exporter.py::TestToMarkdown::test_creates_markdown_file PASSED [ 61%]
tests/unit/test_exporter.py::TestToMarkdown::test_contains_gfm_table PASSED [ 64%]
tests/unit/test_exporter.py::TestToMarkdown::test_contains_korean_text PASSED [ 66%]
tests/unit/test_exporter.py::TestToMarkdown::test_contains_image_reference PASSED [ 69%]
tests/unit/test_exporter.py::TestToMarkdown::test_contains_page_headers PASSED [ 71%]
tests/unit/test_exporter.py::TestToText::test_creates_text_file PASSED   [ 73%]
tests/unit/test_exporter.py::TestToText::test_contains_all_text_content PASSED [ 76%]
tests/unit/test_exporter.py::TestToText::test_contains_page_markers PASSED [ 78%]
tests/unit/test_exporter.py::TestToText::test_table_rows_tab_separated PASSED [ 80%]
tests/unit/test_exporter.py::TestGenerateAllExports::test_generates_all_three_files PASSED [ 83%]
tests/unit/test_parser.py::TestLanguageDetection::test_detect_korean PASSED [ 85%]
tests/unit/test_parser.py::TestLanguageDetection::test_detect_english PASSED [ 88%]
tests/unit/test_parser.py::TestLanguageDetection::test_detect_chinese PASSED [ 90%]
tests/unit/test_parser.py::TestLanguageDetection::test_detect_japanese PASSED [ 92%]
tests/unit/test_parser.py::TestLanguageDetection::test_empty_text_returns_none PASSED [ 95%]
tests/unit/test_parser.py::TestParsePdf::test_parse_pdf_returns_correct_schema PASSED [ 97%]
tests/unit/test_parser.py::TestParsePdf::test_parse_pdf_missing_docling_raises_runtime_error PASSED [100%]

============================= 42 passed in 1.50s ==============================
```

## Bugs Found

### Critical
None.

### High

**H1 — Race condition: DELETE while job is running (no status guard)**
File: `src/backend/routes/results.py`, `delete_job()` lines 100–117.
`DELETE /api/jobs/{job_id}` contains no check against `job.status == "running"`. If a client calls DELETE while `_run_parse_job` is actively parsing, `shutil.rmtree` removes the job directory while the background task is writing export files to it. The background task subsequently finds the job DB row deleted (`None`), hits the except block (AttributeError on `None.status`), and silently terminates. The task consumes CPU/memory for the rest of its execution with no usable output. In production with large PDFs (2–5 minute parse times), this is a realistic scenario.
**Recommended fix:** Add `if job.status == "running": raise HTTPException(status_code=409, detail="Cannot delete a job that is currently running")` before the filesystem cleanup.

### Medium

**M1 — Orphan export files on disk if `generate_all_exports` fails after `parse_pdf` succeeds**
File: `src/backend/routes/upload.py`, `_run_parse_job()` lines 49–65.
If `generate_all_exports` raises (e.g. disk full, permissions error), the except block calls `db.rollback()`, re-queries the job, and marks it `"failed"`. But the three export files may have been partially written to `uploads/{job_id}/` before the exception. No cleanup of these files occurs in the error path. Over time, failed jobs accumulate orphan export files.
**Recommended fix:** In the except block, after marking the job failed, attempt to clean up any partially-written export files: remove `result.json`, `result.md`, `result.txt` from the job directory if they exist.

**M2 — GFM table cells containing `|` character are not escaped**
File: `src/backend/services/exporter.py`, `_table_rows_to_gfm()` lines 16–30.
Cell values with a literal `|` (e.g. from a PDF with table cells like `"Option A | B"`) are inserted verbatim into the GFM row. This produces extra column separators, breaking table alignment and rendering in GitHub, VS Code, and any strict GFM renderer. Example: `[['Col|A', 'B'], ['v|1', 'v2']]` produces `| Col|A | B |` which renders as a 3-column row in a 2-column table.
**Recommended fix:** In `_table_rows_to_gfm`, replace `str(cell)` with `str(cell).replace("|", "\\|")` for both header and data rows.

### Low

**L1 — `shutil.rmtree(ignore_errors=True)` in DELETE silently swallows filesystem errors**
File: `src/backend/routes/results.py` line 108.
If a permission error or file lock prevents directory removal (common on Windows with open file handles), the DB rows are deleted but filesystem artifacts remain. The caller receives HTTP 200 with `{"detail": "Job deleted"}` with no indication that the filesystem cleanup failed. This can lead to silent disk space leakage.
**Recommended fix:** Remove `ignore_errors=True`, catch `OSError` explicitly, and either log the error and continue (returning a warning in the response body) or return HTTP 500.

**L2 — Download integration tests accept 404 as a passing assertion**
File: `tests/integration/test_api.py`, `TestDownloads` class, lines 203–235.
All four download tests use `assert resp.status_code in (200, 404)`. If the download feature were completely broken and always returned 404, these tests would still pass. The assertions inside the `if resp.status_code == 200:` blocks are silently skipped. This creates false confidence: a test suite that reports green but does not actually validate the download feature end-to-end.
**Recommended fix:** Poll for job completion (as `test_get_result_returns_pages_and_metadata` already does), then assert `resp.status_code == 200` unconditionally before checking content.

**L3 — `result["metadata"]["total_pages"]` uses direct dict access that can crash with opaque error**
File: `src/backend/routes/upload.py`, `_run_parse_job()` line 53.
`job.page_count = result["metadata"]["total_pages"]` will raise `KeyError` if the parser returns a result missing either key. This is caught by the broad `except Exception` block and the job is marked `"failed"` with the error message `"'total_pages'"` — providing no useful context.
**Recommended fix:** Use `result.get("metadata", {}).get("total_pages")` with a fallback of `None` to match the nullable DB column type.

**L4 — `test_delete_job_cleans_filesystem` does not verify filesystem cleanup**
File: `tests/integration/test_api.py`, `TestDelete`, lines 253–264.
The test name implies it verifies filesystem cleanup, but the body only asserts that the job is absent from the DB via `GET /api/jobs/{job_id}` returning 404. There is no assertion that `upload_dir / job_id` was removed from disk.
**Recommended fix:** Capture the upload path from the test's `upload_dir` fixture, then after DELETE assert `not (upload_dir / job_id).exists()`.

**L5 — Data rows wider than the header row produce malformed GFM tables**
File: `src/backend/services/exporter.py`, `_table_rows_to_gfm()`.
The function pads shorter data rows but does not truncate rows with more columns than the header. A data row `['1', '2', '3']` with header `['A', 'B']` produces `| 1 | 2 | 3 |` — a row with 3 cells in a 2-column table, which is invalid GFM. This can happen with malformed PDF tables where docling extracts inconsistent row widths.
**Recommended fix:** Truncate cells to `len(header)`: `cells = cells[:len(header)]` after the existing padding logic.

## Detailed Code Review

### What Went Well

1. **Complete contract coverage.** All 10 testable success criteria from the Sprint 2 contract are implemented and verified with real test output.

2. **Clean exporter service design.** `services/exporter.py` is a pure service with no DB, HTTP, or framework dependencies. All three export functions follow a consistent `(result: dict, output_path: Path) -> Path` signature. Easy to unit-test in isolation and simple to reason about.

3. **Graceful handling of missing keys.** All three exporter functions use `.get("pages", [])` and `.get("elements", [])` throughout, so a malformed or empty result dict does not raise an exception — it produces an empty but valid output file. Verified by probe testing with `{}`, `{"metadata": {}}`, and `{"pages": []}` inputs.

4. **Correct FK deletion ordering.** `delete_job` deletes `ParsedResult` before `Job`, respecting the foreign key constraint. No risk of integrity errors even without cascades.

5. **Helper function reuse in results.py.** `_get_job_or_404` and `_get_result_or_404` eliminate repeated error-handling logic across four endpoint handlers, keeping each handler short and focused.

6. **Unicode-safe export throughout.** `json.dump(..., ensure_ascii=False)` and `open(..., encoding="utf-8")` are used consistently in all three export functions. Korean/CJK characters are preserved in all output formats. Verified by `test_preserves_unicode` and `test_contains_korean_text`.

7. **File existence check before FileResponse.** All three download endpoints check `Path(parsed.xxx_path).exists()` before returning `FileResponse`. If the export file was deleted from disk after the DB record was created, a clear 404 is returned rather than a cryptic server error.

8. **Corrupt result_json handled gracefully.** `get_result` wraps `json.loads` in `try/except (json.JSONDecodeError, TypeError)` and returns HTTP 500 with a clear message instead of crashing.

9. **All files comply with 300-line limit.** Longest file is `tests/integration/test_api.py` at 264 lines. All backend source files are under 130 lines.

10. **CORS correctly configured.** `allow_origins=["http://localhost:5173", "http://localhost:3000"]` covers the Vite dev server (5173 per spec) plus an alternative port.

11. **15 new unit tests for exporter.** Covers `to_json`, `to_markdown`, `to_text`, `generate_all_exports`, and `_table_rows_to_gfm` with meaningful assertions including Unicode, page headers, GFM table syntax, and parent directory creation.

### Needs Improvement

1. **DELETE endpoint has no guard against running jobs (H1).** The most likely real-world crash scenario. Should be addressed before Sprint 3 ships.

2. **Download tests are structurally non-validating (L2).** The `in (200, 404)` pattern means the download feature could be entirely broken and tests would still pass. This is the most important test-quality issue.

3. **GFM pipe escaping omitted (M2).** A correctness bug that will manifest silently for any PDF with table cells containing `|`. Easy to fix in one line.

4. **No test for `"failed"` job status flow.** There is no test that mocks `parse_pdf` to raise an exception and verifies the job transitions to `"failed"` with a populated `error_message`. The error recovery path in `_run_parse_job` is never exercised by any test.

5. **`test_delete_job_cleans_filesystem` does not test the filesystem (L4).** The test name creates false documentation that FS cleanup is covered. It only tests DB removal.

6. **No rate limiting on upload endpoint.** Repeated uploads can exhaust disk space and CPU. Acceptable for MVP, but worth noting before public deployment.

## Required Fixes for FAIL (in priority order)

Sprint 2 result is PASS. The following fixes are required before Sprint 3 is considered complete:

1. **(H1 — High, pre-Sprint 3)** Add `status == "running"` guard to `DELETE /api/jobs/{job_id}`. Return HTTP 409 Conflict. File: `src/backend/routes/results.py`, `delete_job()`.

2. **(L2 — Testing, pre-Sprint 3)** Fix download integration tests to poll for completion before asserting download responses. Replace `assert resp.status_code in (200, 404)` with unconditional `assert resp.status_code == 200` after status poll. File: `tests/integration/test_api.py`.

3. **(M2 — Medium, pre-Sprint 3)** Escape `|` characters in `_table_rows_to_gfm` cell values: `str(cell).replace("|", "\\|")`. File: `src/backend/services/exporter.py`.

4. **(M1 — Medium, nice-to-have)** Add export file cleanup to the `except` block in `_run_parse_job` for the case where `generate_all_exports` raises after `parse_pdf` succeeds. File: `src/backend/routes/upload.py`.

5. **(L3 — Low)** Replace `result["metadata"]["total_pages"]` with `result.get("metadata", {}).get("total_pages")` in `_run_parse_job`. File: `src/backend/routes/upload.py`.
