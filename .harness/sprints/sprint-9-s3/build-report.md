# Sprint 9 Feature Sprint 3 Build Report: Engine Selector UI + Upload Integration

## Status: COMPLETE

## What was implemented

### Frontend
1. **EngineSelector.tsx** — Three option cards (Docling, PaddleOCR 3, Gemini Flash) with radio semantics, aria-checked, aria-disabled, data-engine attributes. Gemini locked with lock icon + Settings link when unconfigured.
2. **Sidebar.tsx** — EngineSelector integrated above upload button; `getApiKeyStatus()` fetched on mount; selected engine passed to `upload(file, selectedEngine)`; Settings nav link in footer
3. **useUpload.ts** — `upload()` accepts optional `engine` parameter, passes to `uploadPdf()`
4. **api.ts** — `uploadPdf()` accepts optional `engine` parameter, appends to FormData

### Tests
- **e2e/engine-selector.spec.ts** — 8 E2E tests all pass:
  - Three engine cards render with correct labels
  - Docling selected by default
  - Clicking PaddleOCR selects it (aria-checked)
  - Gemini has aria-disabled when not configured
  - Gemini shows Settings link when locked
  - Settings nav link visible
  - /settings page renders API key form
  - Upload sends engine=paddleocr when PaddleOCR selected
- **e2e/fixtures.ts** — Added `engine` field to all mock jobs
- **e2e/helpers.ts** — Added `api/settings/api-keys` mock

## Test Results
- 8/8 new E2E tests pass
- 37/37 total E2E tests pass (no regressions)
- 127/127 backend tests pass
- Frontend build: 0 errors, 0 warnings
