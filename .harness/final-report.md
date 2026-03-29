# Final Report: Sprint 9 — OCR VL Engine Selection (PaddleOCR 3 + Gemini Flash)

## All Sprints: PASS (3/3)

## Implemented Features

### Sprint 1: Engine Abstraction + PaddleOCR Backend
- `engine` column on Job model (docling/paddleocr/gemini, default "docling")
- `parse_duration_seconds` column tracking wall-clock parse time
- Engine dispatch in `_run_parse_job` with deferred imports
- `POST /api/upload` accepts optional `engine` form field
- `POST /api/jobs/{id}/reprocess` accepts optional `engine` JSON body override
- `GET /api/jobs` / `GET /api/jobs/{id}` include `engine` and `parse_duration_seconds`
- `parser_paddleocr.py` — PaddleOCR 3 adapter (pypdfium2 page rendering, title heuristic, v2 schema, import guard)
- `parser_gemini.py` — stub with import + API key guard
- Frontend `JobSummary` TypeScript interface updated with `engine: EngineType`

### Sprint 2: Gemini Flash Parser + Settings API + Settings UI
- `parser_gemini.py` — full implementation: pypdfium2 → base64 PNG → gemini-2.0-flash → markdown→elements converter
- `GET /api/settings/api-keys` → `{ gemini_configured: bool }` (never exposes raw key)
- `POST /api/settings/api-keys` — writes to `.env` via python-dotenv `set_key()`, updates in-process config
- `SettingsPage.tsx` — API key input form with 3-second "Saved" inline badge
- `/settings` route in React Router
- "Settings" nav link with active state in Sidebar footer
- Engine pill in `MetadataBar` (indigo-50/indigo-700 for PaddleOCR, violet-50/violet-700 for Gemini)
- Engine label in `SidebarDocItem` for non-docling engines

### Sprint 3: Engine Selector UI + Upload Integration
- `EngineSelector.tsx` — three radio-style cards with `aria-checked`, `aria-disabled`, `data-engine` attributes
- Gemini card locked with lock icon + amber "→ Settings" link when key not configured
- `Sidebar.tsx` — EngineSelector wired with selected engine state + `getApiKeyStatus()` on mount
- `useUpload.ts` / `api.ts` — `upload(file, engine?)` passes engine to `POST /api/upload` FormData
- 8 Playwright E2E tests (engine selector scenarios, Gemini locked state, upload with PaddleOCR)

## Final Test Results
- **Backend:** 127/127 pytest tests pass
- **E2E:** 37/37 Playwright tests pass (0 regressions)
- **Frontend build:** 0 TypeScript errors, 0 ESLint warnings

## Known Limitations
- PaddleOCR 3 produces text-only elements (no semantic labels beyond title heuristic)
- Gemini sends pages sequentially with 0.5s delay — slow for large PDFs
- PaddleOCR requires manual `pip install paddleocr>=3.0.0` (optional, import-guarded)
- Gemini requires manual `pip install google-generativeai>=0.8.0` (optional, import-guarded)

## Future Improvements
- PaddleOCR language hint UI (CJK vs EN mode)
- Async/batched Gemini page submission for large PDFs
- Inline API key test button in Settings
- Per-engine advanced configuration options
