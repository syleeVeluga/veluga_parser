# Evaluation Report - Sprint 9 / Feature Sprint 1
Generated: 2026-03-29

## Overall Result: PASS

## Scores
| Category        | Score | Weight | Weighted |
|----------------|-------|--------|---------|
| Design Quality  | N/A   | 20%    | — (no new UI pages in Sprint 1) |
| Originality     | N/A   | 15%    | — (no new UI pages in Sprint 1) |
| Functionality   | 95    | 20%    | 19.0    |
| Code Quality    | 88    | 15%    | 13.2    |
| Craft           | 85    | 10%    | 8.5     |
| Testing         | 95    | 10%    | 9.5     |
| Security        | 85    | 10%    | 8.5     |
| **Total (adjusted, excl. design/originality)** | | | **~87 / 55 applicable pts** |

Note: Design Quality and Originality are not scored this sprint. Sprint 1 is a pure backend
architecture sprint. No new UI pages or components were added; the only frontend change is a
TypeScript type update in `api.ts`. Design scoring resumes from Sprint 2 onward.

---

## Test Output (verbatim)

### `pytest tests/integration/test_engine_dispatch.py -v`
```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: D:\dev\veluga_parser
configfile: pytest.ini

tests/integration/test_engine_dispatch.py::test_default_engine_is_docling PASSED [ 16%]
tests/integration/test_engine_dispatch.py::test_engine_paddleocr_stored PASSED [ 33%]
tests/integration/test_engine_dispatch.py::test_engine_gemini_stored PASSED [ 50%]
tests/integration/test_engine_dispatch.py::test_invalid_engine_defaults_to_docling PASSED [ 66%]
tests/integration/test_engine_dispatch.py::test_engine_appears_in_job_list PASSED [ 83%]
tests/integration/test_engine_dispatch.py::test_paddleocr_raises_runtime_error_when_not_installed PASSED [100%]

============================== 6 passed in 1.17s ==============================
```

### Full test suite `pytest tests/ --ignore=tests/e2e -v`
```
collected 122 items

tests/integration/test_api.py::TestHealth::test_health_returns_ok PASSED
tests/integration/test_api.py::TestUpload::test_upload_pdf_returns_job_id PASSED
tests/integration/test_api.py::TestUpload::test_upload_non_pdf_rejected PASSED
tests/integration/test_api.py::TestUpload::test_upload_pdf_by_extension_accepted PASSED
tests/integration/test_api.py::TestJobStatus::test_get_nonexistent_job_returns_404 PASSED
tests/integration/test_api.py::TestJobStatus::test_upload_then_get_job_status PASSED
tests/integration/test_api.py::TestJobStatus::test_list_jobs_returns_paginated_result PASSED
tests/integration/test_api.py::TestJobStatus::test_list_jobs_pagination_params PASSED
[... all 122 tests ...]
tests/integration/test_engine_dispatch.py::test_paddleocr_raises_runtime_error_when_not_installed PASSED
tests/unit/test_parser.py::TestParsePdf::test_chunks_is_empty_dict PASSED

============================== 122 passed in 3.55s ==============================
```

### Frontend lint
```
> eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0
(exit 0 — zero warnings, zero errors)
```

### Frontend build
```
> tsc && vite build
vite v8.0.3 building client environment for production...
994 modules transformed.
dist/index.html            0.46 kB
dist/assets/index.css     35.55 kB
dist/assets/index.js     953.38 kB
built in 926ms
(chunk size warning only — pre-existing, not a build error)
```

### App import check
```
python -c "from src.backend.main import app; print('OK')"
OK
```

### Live API spot-check
```
curl -s http://localhost:8099/health
{"status":"ok"}

curl -s http://localhost:8099/api/jobs
{
  "total": 2,
  "page": 1,
  "limit": 20,
  "items": [
    {
      "job_id": "def6fc6d-5fbe-4ee2-845b-35596578633f",
      "filename": "붙임1. ...",
      "status": "completed",
      "engine": "docling",
      "parse_duration_seconds": null,
      ...
    },
    {
      "job_id": "2f048f3b-...",
      "status": "completed",
      "engine": "docling",
      "parse_duration_seconds": null,
      ...
    }
  ]
}
```

---

## Contract Verification

| Contract Item | Result | Evidence |
|---|---|---|
| 1. POST /api/upload no engine → GET /api/jobs/{id} returns `"engine": "docling"` | PASS | `test_default_engine_is_docling` passes; `upload.py` line 134 `Form(default="docling")` |
| 2. POST /api/upload with `engine=paddleocr` → job engine is `"paddleocr"` | PASS | `test_engine_paddleocr_stored` passes; dispatches to `parser_paddleocr.parse_pdf_paddleocr` |
| 3. POST /api/upload with `engine=gemini` → job engine is `"gemini"` | PASS | `test_engine_gemini_stored` passes; gemini stored on Job row |
| 4. `pytest tests/integration/test_engine_dispatch.py` all pass | PASS | 6/6 tests pass (verbatim above) |
| 5. GET /api/jobs includes `engine` field on each item | PASS | `test_engine_appears_in_job_list` passes; live curl confirms `"engine": "docling"` on each item |
| 6. PaddleOCR import-guarded: app starts without paddleocr installed | PASS | `parser_paddleocr.py` lines 96-103; `test_paddleocr_raises_runtime_error_when_not_installed` passes; app import returns OK |
| 7. `JobSummary` TypeScript interface has `engine` field | PASS | `api.ts` line 143 `engine: EngineType`; `EngineType = 'docling' \| 'paddleocr' \| 'gemini'` at line 130 |

All 7 contract items verified independently. All PASS.

---

## Playwright UI Evidence

No new UI pages introduced in Sprint 1. The only frontend change is a TypeScript type addition to
`api.ts` (`EngineType` and `engine` field on `JobSummary`). Playwright screenshots are not
applicable this sprint and will resume from Sprint 2 (Settings page) and Sprint 3 (EngineSelector).

---

## Context7 Library Checks

Not invoked. Library usage in this sprint follows standard documented patterns:
- `fastapi.Form` — optional form field with default, correct usage
- `sqlalchemy` `mapped_column(String(20), Float, nullable)` — standard
- `pypdfium2` — deferred import inside function body, correct for optional dep
- `paddleocr.PaddleOCR` — deferred import inside `parse_pdf_paddleocr()`, correct import-guard pattern

No non-standard patterns warranting doc consultation were found.

---

## Bugs Found

### Critical
None.

### High
None.

### Medium

1. **Silent engine init fallback in `parser_paddleocr.py:109-111`** — If `PaddleOCR(lang="ch")` raises
   an exception during model initialization, the code silently falls back to `lang="en"` with no
   log message. A network failure downloading the CJK model would cause English-only OCR with no
   indication. Add `logger.warning(...)` on the except branch.
   File: `src/backend/services/parser_paddleocr.py`, lines 109-111.

2. **`parser_gemini.py` stub raises bare `NotImplementedError` at runtime** — Submitting a real PDF
   with `engine=gemini` will result in a failed job with message "Gemini parser full implementation
   is available in Sprint 2." This is in-scope behavior for Sprint 1, but the failure message
   written to `job.error_message` may confuse users who cannot see the source code. Sprint 2 resolves this.

3. **`parse_duration_seconds` is null on all pre-migration jobs** — All jobs created before this
   sprint show `"parse_duration_seconds": null`. Expected; column is nullable. No action needed in
   Sprint 1.

### Low

1. **Double null-guard on `job.engine` in `upload.py:52` and `jobs.py:40`** — Both use
   `getattr(job, "engine", "docling") or "docling"`. Since the column is `Mapped[str]` non-nullable
   with default `"docling"`, the guard cannot fire for any job created after Sprint 1. Harmless
   but clutters the intent.

2. **`reprocess` response does not echo the new engine** — `POST /api/jobs/{id}/reprocess` with an
   engine override returns only `{"job_id": ..., "status": "pending"}`. Caller must poll
   `GET /api/jobs/{id}` to verify the engine was applied. Low UX impact.

3. **Vite build chunk size warning** — `dist/assets/index.js` is 953 kB. Pre-existing; not
   introduced by this sprint.

---

## Code Review Findings

### Positive

- `upload.py` — Engine validation (`if engine not in _VALID_ENGINES: engine = "docling"`) is clean
  and consistent with the contract requirement.
- `parser_paddleocr.py` — Import guard uses the correct deferred-import pattern inside the function
  body rather than at module level. `pypdfium2` rendering is similarly deferred, ensuring the
  module can be imported even if neither dependency is present.
- `models/job.py` — New columns declared with proper SQLAlchemy typed mapping, nullable semantics
  are correct (`parse_duration_seconds` nullable, `engine` non-nullable with default).
- `tests/integration/test_engine_dispatch.py` — Module-scoped fixture, isolated test DB, correct
  mock patching at the right depth. The `builtins.__import__` patch for the import-guard test is
  technically sound with proper cleanup in `finally`.

### Issues

- `src/backend/routes/upload.py:52` — Redundant `getattr(...) or "docling"` guard on `job.engine`.
  The value was just explicitly stored on the row two lines above.
- `src/backend/routes/jobs.py:40` — Same redundant guard in `_job_to_dict`. Can be simplified to
  `job.engine` after Sprint 1 establishes the column as non-nullable.
- `src/backend/services/parser_paddleocr.py:109-111` — Missing warning log on fallback from
  Chinese to English OCR model.

---

## Required Fixes (if FAIL)

N/A — all contract items verified, zero critical bugs, all 122 tests pass.

---

## Design Recommendation

Sprint 1 is backend-only. For Sprint 2, the key design work will be:
- Settings page: follow Stripe Docs aesthetic (clean form, generous whitespace, indigo Save button)
- Engine pills on job cards: implement the exact color mapping from the spec:
  neutral-700/neutral-100 for Docling, indigo-700/indigo-50 for PaddleOCR, violet-700/violet-50
  for Gemini. Do not substitute with generic Tailwind defaults.
- No gradient backgrounds, no rounded-2xl, no placeholder UI chrome.

Recommendation for Sprint 2 design: **Establish direction** (first sprint with visible UI work).
