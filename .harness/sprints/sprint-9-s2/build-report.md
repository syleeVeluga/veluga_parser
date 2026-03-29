# Sprint 9 Feature Sprint 2 Build Report: Gemini Parser + Settings API + UI

## Status: COMPLETE

## What was implemented

### Backend
1. **parser_gemini.py** — Full Gemini Flash adapter: pypdfium2 page rendering, base64 PNG, gemini-2.0-flash API, markdown→elements converter, rate limiting (0.5s/page), import+key guard, v2 schema
2. **routes/settings.py** — GET/POST /api/settings/api-keys; writes to .env via set_key; updates in-process config; never exposes raw key
3. **main.py** — settings_router registered under /api

### Frontend
- **api.ts** — `getApiKeyStatus()`, `saveGeminiApiKey()`, `ApiKeyStatus` interface
- **SettingsPage.tsx** — API key input form with "Saved" inline badge, configured status indicator
- **main.tsx** — `/settings` route added
- **Sidebar.tsx** — Settings nav link in footer with active state, `useLocation` import
- **MetadataBar.tsx** — Engine pill (indigo/violet/neutral colors)
- **SidebarDocItem.tsx** — Engine label shown for non-docling engines

### Tests
- `tests/integration/test_settings.py` — 5 tests: unconfigured status, key never exposed, key update, empty key 400, set_key called correctly — all pass

## Test Results
- 5/5 settings tests pass
- 127/127 total backend tests pass (no regressions)
- Frontend build: 0 TypeScript errors, 0 warnings
