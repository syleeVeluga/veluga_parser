# Evaluation Report - Sprint 9 Feature Sprint 3

Generated: 2026-03-29

## Overall Result: PASS

## Scores

| Category        | Score (0-100) | Weight | Weighted Score |
|-----------------|---------------|--------|----------------|
| Design Quality  | 78            | 20%    | 15.6           |
| Originality     | 72            | 15%    | 10.8           |
| Functionality   | 98            | 20%    | 19.6           |
| Code Quality    | 92            | 15%    | 13.8           |
| Craft           | 85            | 10%    | 8.5            |
| Testing         | 95            | 10%    | 9.5            |
| Security        | 95            | 10%    | 9.5            |
| **Total**       |               |        | **87.3**       |

---

## Contract Item Results

| Contract Item | Result | Evidence |
|---|---|---|
| EngineSelector renders three cards: "Docling", "PaddleOCR 3", "Gemini Flash" | PASS | Playwright: all three cards visible; `data-engine` attrs confirmed |
| Clicking "PaddleOCR 3" makes it visually selected (aria-checked or data-engine) | PASS | `[data-engine="paddleocr"]` has `aria-checked="true"` after click; Docling transitions to `aria-checked="false"` |
| Gemini card has `aria-disabled="true"` when `gemini_configured` is false | PASS | Playwright with mocked GET returning `gemini_configured: false` confirmed `aria-disabled="true"` |
| Selecting PaddleOCR then uploading → job has `engine: "paddleocr"` in API response | PASS | Live API: `POST /api/upload` with `engine=paddleocr` → `GET /api/jobs/{id}` returns `"engine": "paddleocr"` |
| All existing Playwright specs continue to pass | PASS | 37/37 Playwright tests pass, 0 failures |
| `npm run build` exits 0 | PASS | Build completes in 679ms, 0 errors, 0 warnings |

---

## Test Output (verbatim)

### Playwright (37/37 pass)

```
Running 37 tests using 1 worker

  ok  1 [chromium] › e2e\document-viewer.spec.ts:9:3 › Document Viewer › clicking document in sidebar shows metadata bar (1.3s)
  ok  2 [chromium] › e2e\document-viewer.spec.ts:22:3 › Document Viewer › output tabs switch correctly (1.5s)
  ok  3 [chromium] › e2e\document-viewer.spec.ts:49:3 › Document Viewer › download buttons have correct hrefs (1.0s)
  ok  4 [chromium] › e2e\document-viewer.spec.ts:68:3 › Document Viewer › reprocess button triggers API call (1.0s)
  ok  5 [chromium] › e2e\engine-selector.spec.ts:9:3 › EngineSelector › renders three engine cards with correct labels (942ms)
  ok  6 [chromium] › e2e\engine-selector.spec.ts:17:3 › EngineSelector › Docling card is selected by default (978ms)
  ok  7 [chromium] › e2e\engine-selector.spec.ts:24:3 › EngineSelector › clicking PaddleOCR 3 selects it (1.4s)
  ok  8 [chromium] › e2e\engine-selector.spec.ts:35:3 › EngineSelector › Gemini card has aria-disabled when not configured (1.4s)
  ok  9 [chromium] › e2e\engine-selector.spec.ts:43:3 › EngineSelector › Gemini card shows Settings link when not configured (1.4s)
  ok 10 [chromium] › e2e\engine-selector.spec.ts:51:3 › EngineSelector › Settings nav link is visible in sidebar (1.0s)
  ok 11 [chromium] › e2e\engine-selector.spec.ts:57:3 › EngineSelector › navigating to /settings renders the API key form (1.4s)
  ok 12 [chromium] › e2e\engine-selector.spec.ts:64:3 › EngineSelector › upload sends engine form field to API (1.7s)
  ok 13 [chromium] › e2e\markdown-viewer.spec.ts:13:3 › MarkdownTab Pagination › Prev button is disabled on first page (1.1s)
  ok 14 [chromium] › e2e\markdown-viewer.spec.ts:18:3 › MarkdownTab Pagination › Next button is enabled on first page (1.2s)
  ok 15 [chromium] › e2e\markdown-viewer.spec.ts:23:3 › MarkdownTab Pagination › Next click advances page indicator to 2 / 3 (1.2s)
  ok 16 [chromium] › e2e\markdown-viewer.spec.ts:29:3 › MarkdownTab Pagination › Page content changes after Next click (1.1s)
  ok 17 [chromium] › e2e\markdown-viewer.spec.ts:36:3 › MarkdownTab Pagination › Next button is disabled on last page (1.2s)
  ok 18 [chromium] › e2e\markdown-viewer.spec.ts:44:3 › MarkdownTab Pagination › Prev button is enabled after advancing past page 1 (1.1s)
  ok 19 [chromium] › e2e\markdown-viewer.spec.ts:52:3 › MarkdownTab Pagination › Prev click after Next returns to page 1 content (1.2s)
  ok 20 [chromium] › e2e\markdown-viewer.spec.ts:62:3 › MarkdownTab Pagination › Scroll resets to top after page navigation (1.2s)
  ok 21 [chromium] › e2e\markdown-viewer.spec.ts:77:3 › MarkdownTab Fallback Mode › renders full content when pages endpoint returns 404 (1.0s)
  ok 22 [chromium] › e2e\markdown-viewer.spec.ts:89:3 › MarkdownTab Fallback Mode › page indicator label reads "1 / 3" before any navigation (1.1s)
  ok 23 [chromium] › e2e\markdown-viewer.spec.ts:97:3 › MarkdownTab Full Markdown Fallback Content › MOCK_MARKDOWN contains Parsed Document for legacy fallback (0ms)
  ok 24 [chromium] › e2e\navigation.spec.ts:9:3 › URL Sync & Navigation › empty state shown when no document selected (917ms)
  ok 25 [chromium] › e2e\navigation.spec.ts:15:3 › URL Sync & Navigation › clicking document updates URL (1.1s)
  ok 26 [chromium] › e2e\navigation.spec.ts:21:3 › URL Sync & Navigation › direct navigation to /jobs/:id loads document (958ms)
  ok 27 [chromium] › e2e\navigation.spec.ts:33:3 › URL Sync & Navigation › switching between documents without page reload (1.1s)
  ok 28 [chromium] › e2e\navigation.spec.ts:45:3 › Responsive: Mobile Drawer › sidebar becomes overlay drawer on narrow viewport (944ms)
  ok 29 [chromium] › e2e\navigation.spec.ts:65:3 › Responsive: Mobile Drawer › clicking document on mobile closes drawer (1.0s)
  ok 30 [chromium] › e2e\sidebar.spec.ts:9:3 › Sidebar › renders sidebar with document list on app load (952ms)
  ok 31 [chromium] › e2e\sidebar.spec.ts:28:3 › Sidebar › shows status badges for each document (966ms)
  ok 32 [chromium] › e2e\sidebar.spec.ts:35:3 › Sidebar › collapse/expand via toggle button (1.1s)
  ok 33 [chromium] › e2e\sidebar.spec.ts:53:3 › Sidebar › collapse/expand via Ctrl+B keyboard shortcut (1.1s)
  ok 34 [chromium] › e2e\sidebar.spec.ts:64:3 › Sidebar › sidebar state persists in localStorage (1.5s)
  ok 35 [chromium] › e2e\upload-delete.spec.ts:10:3 › Upload Flow › upload button opens file picker and navigates on success (1.0s)
  ok 36 [chromium] › e2e\upload-delete.spec.ts:84:3 › Delete Flow › delete with confirmation removes document from sidebar (1.1s)
  ok 37 [chromium] › e2e\upload-delete.spec.ts:106:3 › Delete Flow › cancel delete keeps document in list (1.1s)

  37 passed (44.1s)
```

### Backend pytest (127/127 pass)

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 127 items

tests/integration/test_api.py  (37 tests, all PASSED)
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
tests/unit/  (79 tests, all PASSED)

============================= 127 passed in 3.47s =============================
```

### npm run build

```
> veluga-pdf-parser-frontend@1.0.0 build
> tsc && vite build

vite v8.0.3 building client environment for production...
✓ 996 modules transformed.
dist/index.html                              0.46 kB
dist/assets/index-Bjb0u0Oy.css              38.01 kB
dist/assets/index-BVpNlhXf.js              960.65 kB

✓ built in 679ms
(advisory: chunk size > 500kB — not an error)
```

### npm run lint

```
> eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0
(zero output = 0 warnings, 0 errors — PASS)
```

---

## Playwright UI Evidence

### Screenshot 01 — Home page baseline (test-results/sprint9/01_home_baseline.png)
Three engine cards in sidebar: "Docling" selected by default (indigo-500 left-border accent, indigo-50 background, filled radio indicator). "PaddleOCR 3" and "Gemini Flash" unselected. ENGINE uppercase label above cards. Upload PDF button below. Document list with two completed jobs. Settings nav link at bottom.

### Screenshot 02 — PaddleOCR 3 selected (test-results/sprint9/02_paddleocr_selected.png)
After click: PaddleOCR 3 card gains indigo left-border and background. Docling returns to unselected state. Confirmed: `aria-checked="true"` on paddleocr, `aria-checked="false"` on docling.

### Screenshot 03 — Gemini locked state (test-results/sprint9/03_gemini_locked.png)
With `gemini_configured: false` mocked: Gemini Flash card shows at reduced opacity, lock icon (SVG padlock, amber color), and "→ Settings" text link inline. Card is non-interactive.

### Screenshot 04 — Upload with engine (test-results/sprint9/04_upload_with_engine.png)
After selecting PaddleOCR and triggering upload: `engine=paddleocr` confirmed in FormData of intercepted request.

### Screenshot 05 — Settings page (test-results/sprint9/05_settings_page.png)
`/settings` renders a clean card: "Gemini API Key" heading, description, password input (`id="gemini-api-key"`), Save button. Settings nav link highlighted in sidebar footer.

---

## API Verification

### GET /api/settings/api-keys
Response: `{"gemini_configured": true}` — raw key never returned. PASS.

### POST /api/settings/api-keys (empty key)
Response 400: `{"detail": "API key cannot be empty"}`. PASS.

### POST /api/settings/api-keys (whitespace key)
Response 400. PASS.

### POST /api/upload with engine=paddleocr
Response 200: `{"job_id": "e4d68b62-...", "filename": "test.pdf", "status": "pending"}`.
Subsequent `GET /api/jobs/{id}`: `{"engine": "paddleocr", ...}`. PASS.

### GET /api/jobs (job list)
Both existing jobs include `"engine": "docling"` field. PASS.

---

## Library Usage Issues

- React `aria-checked={boolean}`: Renders as `"true"`/`"false"` string in DOM. Correct per WAI-ARIA spec for `role="radio"`.
- `aria-disabled={disabled ? 'true' : undefined}`: Correctly omits attribute when not disabled (preferred over `aria-disabled="false"`). Correct pattern.
- `dotenv.set_key()` in `settings.py`: Standard usage per python-dotenv docs. No deprecated API.

---

## Bugs Found

### Critical
None.

### High
None.

### Medium
None.

### Low
- `src/frontend/src/services/api.ts` is at exactly 299 lines. One additional function would breach the 300-line CLAUDE.md limit. Consider splitting in a future sprint.
- `uploadPdf()` does not append `engine` when value is `'docling'` (falsy check `if (engine)` passes for all three engine strings since none are falsy). Actually this is fine — all three EngineType values are truthy strings. No actual bug.

---

## Code Review Findings

### Strengths
- `EngineSelector.tsx` (82 lines): Self-contained, single responsibility. Clean separation of ENGINES constant from render logic.
- State lifting to `Sidebar.tsx`: Correct architecture per contract's technical decisions.
- `useUpload.ts`: Clean optional parameter threading. `engine?: EngineType` signature is correct TypeScript.
- `settings.py`: Catches `PermissionError` separately from generic exceptions with appropriate HTTP codes and actionable error messages.
- `aria-disabled={disabled ? 'true' : undefined}` avoids the anti-pattern of `aria-disabled="false"` which some AT interpret differently.

### Issues
- `src/frontend/src/components/EngineSelector.tsx:43` — The selected card class string `border-l-4 border-indigo-500 bg-indigo-50 border-r border-t border-b border-indigo-200` mixes `border-l-4` (4px) with `border-r border-t border-b` (1px sides). Tailwind's shorthand `border` would conflict, but since the individual sides are specified explicitly, the result is correct in practice. Still fragile — prefer `border border-indigo-200 border-l-4 border-l-indigo-500` ordering for clarity.

---

## Required Fixes for FAIL

None — result is PASS.

---

## Design Recommendation

**Refine current direction.** The engine selector integrates cohesively with the existing developer-tool aesthetic. The indigo accent, amber lock state, and compact card layout are deliberate choices that align with the spec's stated design direction. Future refinements to consider:
- Engine pills on job cards (spec-stated but not part of Sprint 3 criteria — queued for polish pass).
- A very short selection transition (50ms) on engine cards to make toggling feel more tactile.
- The sidebar is approaching visual density; consider a collapsible engine section in a future sprint if more engines are added.

---

## Summary

All 6 contract criteria independently verified through Playwright, live API calls, and code review. Weighted total 87.3/100 exceeds the 70% threshold. All individual categories exceed 50%. Zero critical or high bugs. Zero test failures.
