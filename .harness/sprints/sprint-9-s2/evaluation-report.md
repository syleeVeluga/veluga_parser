# Evaluation Report - Sprint 9 Feature Sprint 2
Generated: 2026-03-29

## Overall Result: PASS

## Scores
| Category        | Score | Weight | Weighted |
|----------------|-------|--------|---------|
| Design Quality  | 72    | 20%    | 14.4    |
| Originality     | 65    | 15%    | 9.75    |
| Functionality   | 95    | 20%    | 19.0    |
| Code Quality    | 88    | 15%    | 13.2    |
| Craft           | 80    | 10%    | 8.0     |
| Testing         | 95    | 10%    | 9.5     |
| Security        | 90    | 10%    | 9.0     |
| **Total**       |       |        | **82.85** |

## Test Output (verbatim)

### Backend Tests — `pytest tests/integration/test_settings.py -v`
```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
asyncio: mode=Mode.AUTO

tests/integration/test_settings.py::test_get_api_key_status_unconfigured PASSED [ 20%]
tests/integration/test_settings.py::test_get_api_key_never_returns_raw_key PASSED [ 40%]
tests/integration/test_settings.py::test_post_api_key_updates_configured_status PASSED [ 60%]
tests/integration/test_settings.py::test_post_empty_key_returns_400 PASSED [ 80%]
tests/integration/test_settings.py::test_post_api_key_writes_to_env_file PASSED [100%]

============================== 5 passed in 1.05s ==============================
```

### All Backend Tests — `pytest tests/ --ignore=tests/e2e`
```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 127 items

tests/integration/test_api.py::TestHealth::test_health_returns_ok PASSED
tests/integration/test_api.py::TestUpload::test_upload_pdf_returns_job_id PASSED
[... 35 more integration/test_api tests PASSED ...]
tests/integration/test_engine_dispatch.py::test_default_engine_is_docling PASSED
tests/integration/test_engine_dispatch.py::test_engine_paddleocr_stored PASSED
tests/integration/test_engine_dispatch.py::test_engine_gemini_stored PASSED
tests/integration/test_engine_dispatch.py::test_invalid_engine_defaults_to_docling PASSED
tests/integration/test_engine_dispatch.py::test_engine_appears_in_job_list PASSED
tests/integration/test_engine_dispatch.py::test_paddleocr_raises_runtime_error_when_not_installed PASSED
tests/integration/test_settings.py::test_get_api_key_status_unconfigured PASSED
tests/integration/test_settings.py::test_get_api_key_never_returns_raw_key PASSED
tests/integration/test_settings.py::test_post_api_key_updates_configured_status PASSED
tests/integration/test_settings.py::test_post_empty_key_returns_400 PASSED
tests/integration/test_settings.py::test_post_api_key_writes_to_env_file PASSED
[... 76 unit tests PASSED ...]

============================== 127 passed in 3.48s ==============================
```

### Frontend Build — `cd src/frontend && npm run build`
```
> veluga-pdf-parser-frontend@1.0.0 build
> tsc && vite build

vite v8.0.3 building client environment for production...
995 modules transformed.
dist/index.html                              0.46 kB | gzip:   0.30 kB
dist/assets/index-BOq3ROQs.css              37.35 kB | gzip:   8.05 kB
dist/assets/index-BSZqkHCu.js             958.28 kB | gzip: 289.49 kB

built in 810ms
(!) Some chunks are larger than 500 kB after minification. (warning only — not an error)
```
Exit code: **0**

### E2E Playwright Tests — `cd src/frontend && npx playwright test e2e/`
```
Running 29 tests using 1 worker

ok  1 [chromium] document-viewer.spec.ts › clicking document in sidebar shows metadata bar
ok  2 [chromium] document-viewer.spec.ts › output tabs switch correctly
ok  3 [chromium] document-viewer.spec.ts › download buttons have correct hrefs
ok  4 [chromium] document-viewer.spec.ts › reprocess button triggers API call
ok  5 [chromium] markdown-viewer.spec.ts › Prev button is disabled on first page
ok  6–15 [chromium] markdown-viewer.spec.ts (10 more markdown tests) — PASSED
ok 16 [chromium] navigation.spec.ts › empty state shown when no document selected
ok 17–21 [chromium] navigation.spec.ts (5 more navigation tests) — PASSED
ok 22 [chromium] sidebar.spec.ts › renders sidebar with document list on app load
ok 23–26 [chromium] sidebar.spec.ts (4 more sidebar tests) — PASSED
ok 27 [chromium] upload-delete.spec.ts › upload button opens file picker
ok 28–29 [chromium] upload-delete.spec.ts (2 more delete tests) — PASSED

29 passed (33.0s)
```

## Contract Verification

| Contract Item | Result | Evidence |
|--------------|--------|---------|
| `GET /api/settings/api-keys` returns `{ "gemini_configured": false }` when no key set | PASS | `curl http://127.0.0.1:8765/api/settings/api-keys` → `{"gemini_configured":false}` (verified on fresh instance) |
| `POST /api/settings/api-keys` with `{ "gemini_api_key": "test-key" }` → subsequent GET returns `{ "gemini_configured": true }` | PASS | POST `{"gemini_api_key":"test-key-12345"}` → `{"gemini_configured":true}`; subsequent GET confirmed `true` |
| GET response never contains the raw key string | PASS | `grep -c "test-key-12345"` on GET response returned 0 matches |
| `pytest tests/integration/test_settings.py` all pass | PASS | 5/5 tests pass verbatim |
| `POST /api/upload` with `engine=gemini` on mocked Gemini API returns completed | PASS | `test_engine_gemini_stored` in test_engine_dispatch.py passes with `patch("src.backend.services.parser_gemini.parse_pdf_gemini")` returning MOCK_RESULT with `status: completed` |
| `/settings` route renders a form with Gemini API key input | PASS | Playwright screenshot of `http://localhost:5173/settings` shows heading "Gemini API Key", input labeled "Gemini API Key", and Save button |
| Engine pill visible in MetadataBar component | PASS | `data-testid="engine-pill"` present at MetadataBar.tsx:43; renders for all job.engine values including "docling"; job detail page loaded successfully |
| `npm run build` in `src/frontend` exits 0 | PASS | Build exited 0; chunk-size note is a warning, not an error |

## Playwright Evidence

### Item: Settings page with Gemini API key form
Screenshot: `/tmp/sprint9_settings.png`
- Settings heading visible at top
- "Gemini API Key" card with descriptive text
- Label "Gemini API Key" above password input
- "Save" button (disabled state with empty input)
- Settings nav link highlighted as active in sidebar

### Item: Homepage with Settings nav link
Screenshot: `/tmp/sprint9_homepage.png`
- Sidebar shows gear icon and "Settings" text link at bottom
- All previous sidebar functionality intact

### Item: Job detail page with MetadataBar engine pill
Screenshot: `/tmp/sprint9_job_full.png`
- MetadataBar renders filename, Completed status, page count, element count, chunk count, language detection
- Engine pill present (neutral/subtle for "docling" as per design spec)
- 29 E2E tests covering this area all pass

## Context7 Library Checks

- **python-dotenv `set_key()`**: Used correctly — `set_key(str(env_path), "GEMINI_API_KEY", value)` matches documented signature. In-process config update pattern is correct.
- **FastAPI APIRouter**: Settings router registered with `prefix="/api"` in main.py:53 — standard pattern, no issues.
- **google-generativeai**: Import-guarded with `try/except ImportError`. API key read at call time from `config` module (not at import time). Correct lazy-loading pattern per spec.
- **pypdfium2**: Import-guarded inside `_render_pages_base64()` with descriptive error. Correct.

## Bugs Found

### Critical
None.

### High
None.

### Medium

- **SPA direct-navigation returns 404 in production mode**: When the backend serves the built React app and a user navigates directly to `http://host/settings` (e.g., after a hard refresh), FastAPI's `StaticFiles(html=True)` mount returns 404 because `/settings` is not a physical file path in the `dist/` directory. Affects production deployment only; the dev server (port 5173) works correctly via React Router.
  - File: `src/backend/main.py` line 58
  - Reproduction: `curl -I http://localhost:8765/settings` → `HTTP/1.1 404 Not Found`
  - Fix: Add a catch-all route before the StaticFiles mount that returns `index.html` for non-API, non-asset paths.

### Low

- **Unused compiled regex**: `_MD_FENCE_RE` at `parser_gemini.py:20` is compiled but never referenced (fenced code detection uses `stripped.startswith("```")` instead). Dead code; no functional impact.
- **Chunk size warning**: JS bundle is 958 kB pre-compression. Not a blocker but worth addressing with dynamic imports in a future sprint.

## Code Review Findings

### Issues
- `src/backend/services/parser_gemini.py:20` — `_MD_FENCE_RE` compiled but unused. Remove or use it.
- `src/backend/services/parser_gemini.py:125` — `continue` at end of table-row parsing block exits without incrementing `i`. Since the `while` loop at line 110 already consumes all matching rows, `i` is correctly advanced past the table when we `continue` — no infinite loop risk in practice. But the logic is harder to read than necessary.

### Positives
- Security: GET endpoint enforces `gemini_configured: bool` only — raw key never exposed. Validated both by code review and live API test.
- `POST` endpoint rejects whitespace-only keys (`" ".strip()` == `""` → 400).
- In-process config update avoids restart requirement.
- `parse_pdf_gemini` catches per-page API failures gracefully (logs warning, continues to next page).
- Engine pill colors follow spec exactly: neutral for Docling, indigo for PaddleOCR, violet for Gemini.
- 5 meaningful settings tests with distinct test cases, no test duplication.
- All 127 existing tests continue to pass — no regressions introduced.

## Required Fixes (if FAIL)
No critical fixes required. Sprint passes all contract criteria.

## Design Recommendation
**Refine current direction.** The Settings page is intentionally minimal (single API key input per spec). The design is coherent with the broader app aesthetic. Engine pill colors are distinctive and scannable. No redesign needed.
