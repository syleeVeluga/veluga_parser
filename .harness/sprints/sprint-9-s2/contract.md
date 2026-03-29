# Sprint 2 Contract: Gemini Flash Parser + Settings API + API Key Management UI

## Goal
Gemini Flash engine usable end-to-end when an API key is configured; Settings page navigable and persists the key. Engine pill displayed on job cards.

## Implementation Goals
1. Implement `src/backend/services/parser_gemini.py` with full `parse_pdf_gemini()` function
2. `src/backend/routes/settings.py` — `GET /api/settings/api-keys` and `POST /api/settings/api-keys`
3. Register settings router in `main.py` under `/api`
4. `src/tests/test_settings.py` — pytest tests for key storage and retrieval
5. `src/frontend/src/pages/SettingsPage.tsx` — Gemini API key input form
6. Add `/settings` route to React Router config
7. Add "Settings" nav link in `AppShell`/`Sidebar`
8. `getApiKeyStatus()` and `saveGeminiApiKey()` added to `api.ts`
9. Engine pill display in `MetadataBar` and `SidebarDocItem`/job list rows

## Success Criteria (each independently testable)
- `GET /api/settings/api-keys` returns `{ "gemini_configured": false }` when no key set
- `POST /api/settings/api-keys` with `{ "gemini_api_key": "test-key" }` → subsequent GET returns `{ "gemini_configured": true }`
- GET response never contains the raw key string
- `pytest tests/integration/test_settings.py` all pass
- `POST /api/upload` with `engine=gemini` on mocked Gemini API returns `status: "completed"`
- Navigating to `/settings` renders a form with Gemini API key input (Playwright)
- Engine pill visible on job detail metadata bar
- `npm run build` in `src/frontend` exits 0

## Out of Scope
- Frontend engine selector in upload flow (Sprint 3)

## Technical Decisions
- Settings key stored in `BASE_DIR/.env` via `python-dotenv set_key()`; config module updated in-process
- GET endpoint returns only `gemini_configured: bool`, never raw key
- Gemini parser: pypdfium2 page rendering → base64 PNG → gemini-2.0-flash vision API → markdown → elements
- Engine pill: indigo-50/indigo-700 for PaddleOCR, violet-50/violet-700 for Gemini, neutral for Docling
- Settings save shows inline "Saved" badge (auto-hides after 3s) — no toast library needed
