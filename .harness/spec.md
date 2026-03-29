# Feature Spec: OCR VL Engine Selection (PaddleOCR 3 + Gemini Flash)

## Overview
Extend the veluga_parser extraction pipeline with two additional Vision-Language OCR engines:
PaddleOCR 3 (local installation) and Google Gemini Flash API. Users select their preferred engine
per upload via a compact engine-selector UI embedded in the upload flow. A Settings panel
stores the Gemini API key persistently in the backend `.env` file.

## Feature Requirements

### Must-Have
- [ ] `EngineType` enum with values `docling`, `paddleocr`, `gemini` persisted on the Job model
- [ ] `parse_pdf_paddleocr()` function in `src/backend/services/parser_paddleocr.py` producing the same v2 result dict schema as `parse_pdf()`
- [ ] `parse_pdf_gemini()` function in `src/backend/services/parser_gemini.py` producing the same v2 result dict schema
- [ ] `upload.py` accepts optional `engine` form field (`docling` | `paddleocr` | `gemini`) defaulting to `docling`
- [ ] `upload.py` `_run_parse_job` dispatches to the correct parser based on stored engine
- [ ] `POST /api/settings/api-keys` endpoint — save Gemini API key to server `.env` file and reload config
- [ ] `GET /api/settings/api-keys` endpoint — return `{ gemini_configured: bool }` (never return the raw key)
- [ ] Engine selector component rendered in `UploadZone` above the drop-zone, with three clearly labelled radio-style option cards
- [ ] Gemini option is greyed-out with a "No API key" warning if Gemini key is not configured
- [ ] Settings page/panel accessible from the app navigation for entering the Gemini API key
- [ ] `engine` field displayed in job list row and job detail metadata bar
- [ ] `reprocess` endpoint accepts optional `engine` override; defaults to job's original engine
- [ ] All new API endpoints covered by pytest integration tests
- [ ] PaddleOCR parser produces elements with the same fields as docling output: `element_id`, `type`, `content`, `page_number`, `reading_order`, `bbox`, `language`
- [ ] Gemini parser sends each PDF page as a base64-encoded image to the Gemini Flash vision API and parses returned markdown into elements

### Nice-to-Have
- [ ] Per-engine processing time recorded in job metadata (`parse_duration_seconds`)
- [ ] Inline API key test button in Settings that calls a lightweight Gemini probe request
- [ ] PaddleOCR language hint passed as a config option (default `["en", "ko", "ja", "ch"]`)
- [ ] Toast notification if user selects Gemini without a configured key and tries to upload

## Technical Design

### Data Models

**Job table — new columns:**
| Column | Type | Default | Notes |
|--------|------|---------|-------|
| `engine` | `String(20)` | `"docling"` | `docling` / `paddleocr` / `gemini` |
| `parse_duration_seconds` | `Float` | `NULL` | wall-clock parse time |

No schema migration file is needed for SQLite dev; `create_tables()` with `checkfirst=True` handles new columns by dropping and recreating in dev. Document that production migration is manual ALTER TABLE.

Decision: engine is stored on the Job row (not on ParsedResult) because it is a property of how the job was requested, not of the result content.

### API Endpoints

| Method | Path | Auth | Request Body / Params | Response |
|--------|------|------|-----------------------|---------|
| POST | `/api/upload` | No | `file` (PDF), `engine` (form field, optional) | existing `UploadResponse` |
| POST | `/api/jobs/{job_id}/reprocess` | No | JSON `{ "engine": "gemini" }` (optional) | `{ job_id, status }` |
| GET | `/api/settings/api-keys` | No | — | `{ "gemini_configured": bool }` |
| POST | `/api/settings/api-keys` | No | JSON `{ "gemini_api_key": "..." }` | `{ "gemini_configured": true }` |

**Engine field in existing responses:**
- `JobSummary` gains `engine: str` field
- `GET /api/jobs/{job_id}` response includes `engine`

### Settings Storage
The Gemini API key is written to a `.env` file at the project root (`BASE_DIR/.env`) using
`python-dotenv`'s `set_key()`. The key name is `GEMINI_API_KEY`. Config module reads it at
startup via `os.getenv("GEMINI_API_KEY", "")`. The `/api/settings/api-keys` POST endpoint
calls `dotenv.set_key()` then updates `config.GEMINI_API_KEY` in-process without a restart.

The key is never returned by any GET endpoint — only the boolean `gemini_configured` is exposed.

### Parser Architecture

**Adapter contract** — all three parsers must return a dict matching this structure (same as
existing `parse_pdf()` return value):
```
{
  "schema_version": "2.0",
  "metadata": { total_pages, languages, has_tables, has_images, has_equations, has_code, title, page_dimensions },
  "toc": [...],
  "elements": [...],
  "pages": [...],
  "chunks": {},
  "page_markdowns": { "1": "...", ... }
}
```

**`src/backend/services/parser_paddleocr.py`**
- Import guard: `try: from paddleocr import PaddleOCR` → raises `RuntimeError` with install hint if missing
- Uses `PaddleOCR(use_angle_cls=True, lang="ch")` for CJK; falls back to `lang="en"` for English
- Renders each PDF page to a PIL image via `pypdfium2` (already a transitive dependency of docling)
- Runs OCR on each page image, collects text blocks with bbox coordinates
- Maps each block to element type `"text"` (PaddleOCR does not provide semantic labels); title heuristic: first block on page 1 with font size significantly larger than median
- Calls `_detect_language()` from `parser.py` (shared utility, imported directly)
- Produces `page_markdowns` as plain concatenated text per page

**`src/backend/services/parser_gemini.py`**
- Import guard: `try: import google.generativeai as genai` → raises `RuntimeError` with install hint
- Reads `GEMINI_API_KEY` from `config` at call time (not import time)
- Renders each PDF page to base64 PNG via `pypdfium2`
- Sends each page image to `gemini-2.0-flash` with a structured prompt requesting markdown output
- Prompt instructs model to preserve headings, tables (as Markdown), and lists; output plain Markdown per page
- Parses returned Markdown per page into elements using a lightweight Markdown-to-elements converter (headings → `section_header`/`title`, paragraphs → `text`, fenced code → `code`, `|...|` tables → `table`)
- Rate-limits: sends pages sequentially with 0.5 s between requests to avoid 429 errors
- `page_markdowns` is set to the raw Markdown returned by Gemini per page

**Dispatch in `upload.py`:**
```python
if job.engine == "paddleocr":
    from src.backend.services.parser_paddleocr import parse_pdf_paddleocr as _parse
elif job.engine == "gemini":
    from src.backend.services.parser_gemini import parse_pdf_gemini as _parse
else:
    from src.backend.services.parser import parse_pdf as _parse
result = _parse(file_path, image_dir)
```

### New Backend Files
- `src/backend/services/parser_paddleocr.py` — PaddleOCR 3 adapter
- `src/backend/services/parser_gemini.py` — Gemini Flash adapter
- `src/backend/routes/settings.py` — API key management endpoints
- `src/tests/test_settings.py` — pytest coverage for settings routes
- `src/tests/test_engine_dispatch.py` — pytest coverage for engine routing

### Frontend Screens

**EngineSelector component** (`src/frontend/src/components/EngineSelector.tsx`)
Three horizontally-arranged option cards, radio-button semantics:
- "Docling" — default, always enabled, subtitle "Local · Multi-lingual"
- "PaddleOCR 3" — always enabled, subtitle "Local · CJK-optimised"
- "Gemini Flash" — enabled only if `gemini_configured === true`; otherwise shows lock icon + "Add API key in Settings"
Emits `onChange(engine: EngineType)`. Selected card has a distinct left-border accent and background.

**UploadZone changes** — accepts `engine` prop; passes it to `uploadPdf()`.
`uploadPdf()` in `api.ts` gains an optional `engine` parameter appended to `FormData`.

**Settings page** (`src/frontend/src/pages/SettingsPage.tsx`)
- Route: `/settings`
- Single card: "Gemini API Key" — password input + Save button
- On save: `POST /api/settings/api-keys`, shows inline success/error feedback
- Uses `GET /api/settings/api-keys` on mount to show current configured state

**Navigation** — add "Settings" link to `AppShell` / `Layout` sidebar or top-nav.

**JobSummary display** — `JobStatusBadge` or `MetadataBar` shows engine as a small pill
(e.g., "Docling", "PaddleOCR", "Gemini").

**api.ts additions:**
```typescript
export type EngineType = 'docling' | 'paddleocr' | 'gemini'
export async function uploadPdf(file: File, engine?: EngineType): Promise<UploadResponse>
export async function getApiKeyStatus(): Promise<{ gemini_configured: boolean }>
export async function saveGeminiApiKey(key: string): Promise<{ gemini_configured: boolean }>
```

## Sprint Plan

### Sprint 1: Engine abstraction + PaddleOCR backend
**Goal:** Swap-in architecture is in place; PaddleOCR parser runs end-to-end and produces a
valid v2 result; `engine` is stored on the Job and returned from the API.

**Scope:**
- [ ] Add `engine` column to `Job` model (SQLAlchemy, String 20, default `"docling"`)
- [ ] Update `upload.py` to accept `engine` form field and store it on the Job row
- [ ] Update `_run_parse_job` with dispatch block (docling / paddleocr / gemini)
- [ ] Implement `src/backend/services/parser_paddleocr.py` with `parse_pdf_paddleocr()`
- [ ] Add `engine` field to `JobSummary` TypedDict / response schema in jobs route
- [ ] Update `reprocess` endpoint to accept optional `engine` JSON body field
- [ ] Write `src/tests/test_engine_dispatch.py` covering: upload with `engine=docling` stores correctly, upload with `engine=paddleocr` stores correctly, dispatch routes to correct parser
- [ ] Update `JobSummary` TypeScript interface with `engine` field

**Success criteria (testable):**
- `POST /api/upload` with `engine=paddleocr` → `GET /api/jobs/{id}` returns `"engine": "paddleocr"`
- `POST /api/upload` with no `engine` field → job `engine` is `"docling"`
- `POST /api/upload` with `engine=paddleocr` on a real PDF completes with `status: "completed"` and `element_count > 0`
- `pytest src/tests/test_engine_dispatch.py` passes (mocking out the heavy parsers)
- Engine field appears in job list JSON response

**Out of scope:** Gemini parser, Settings UI, frontend engine selector

---

### Sprint 2: Gemini Flash parser + Settings API + API key management UI
**Goal:** Gemini Flash engine is usable end-to-end when an API key is configured; Settings page
is navigable and persists the key.

**Scope:**
- [ ] Implement `src/backend/services/parser_gemini.py` with `parse_pdf_gemini()`
- [ ] Add `GEMINI_API_KEY` reading to `src/backend/config.py`
- [ ] Implement `src/backend/routes/settings.py` with `GET /api/settings/api-keys` and `POST /api/settings/api-keys`
- [ ] Register settings router in `main.py` under `/api`
- [ ] Write `src/tests/test_settings.py` covering key storage, retrieval of `gemini_configured` status, key never exposed in GET response
- [ ] Add `SettingsPage.tsx` with Gemini API key input form
- [ ] Add `/settings` route to React Router config
- [ ] Add "Settings" nav link in `AppShell`/`Layout`
- [ ] Implement `getApiKeyStatus()` and `saveGeminiApiKey()` in `api.ts`
- [ ] Add engine pill display to `MetadataBar` and `JobList` rows

**Success criteria (testable):**
- `GET /api/settings/api-keys` returns `{ "gemini_configured": false }` when no key set
- `POST /api/settings/api-keys` with `{ "gemini_api_key": "test-key" }` → subsequent GET returns `{ "gemini_configured": true }`
- GET response never contains the raw key string
- Navigating to `/settings` renders the key input form (Playwright: `page.goto('/settings')` → input with label "Gemini API Key" is visible)
- `POST /api/upload` with `engine=gemini` on a small PDF (mocked Gemini API) completes with `status: "completed"`
- `pytest src/tests/test_settings.py` passes

**Out of scope:** Frontend engine selector in upload flow (that is Sprint 3)

---

### Sprint 3: Engine selector UI + upload integration
**Goal:** Users can choose the extraction engine before uploading; Gemini option is gated by API
key availability; engine is shown on job cards.

**Scope:**
- [ ] Implement `EngineSelector.tsx` component with three option cards
- [ ] Wire `EngineSelector` into `HomePage` / `UploadZone` — selected engine state managed in `HomePage`
- [ ] Update `uploadPdf()` in `api.ts` to accept and pass optional `engine` parameter
- [ ] Update `UploadZone` props to accept `engine` and pass it through to `uploadPdf()`
- [ ] Fetch `gemini_configured` status in `HomePage` (or a new `useEngineConfig` hook) on mount to enable/disable Gemini option
- [ ] Display engine pill in `JobList` row (`SidebarDocItem` and/or table row)
- [ ] Display engine in `MetadataBar` on job detail page
- [ ] Playwright E2E test: engine selector renders, selecting "PaddleOCR 3" then uploading results in a job with `engine: "paddleocr"` in the API response
- [ ] Playwright E2E test: Gemini option is locked when `gemini_configured = false` (mock the settings endpoint)

**Success criteria (testable):**
- Playwright: `EngineSelector` renders three cards with correct labels
- Playwright: clicking "PaddleOCR 3" card makes it visually selected (aria-checked or data-selected)
- Playwright: uploading with PaddleOCR selected → job detail shows "PaddleOCR" pill in metadata
- Playwright: Gemini card has `aria-disabled` when `gemini_configured` is false
- Playwright: navigating to `/settings`, entering a key and saving → Gemini card becomes enabled on `/`
- All existing Playwright specs continue to pass

**Out of scope:** Per-engine advanced options, PaddleOCR language hint UI

---

## Design Direction

**Mood / Identity:** Focused developer tooling — precise, low-distraction, information-dense.
Think "VS Code sidebar meets Notion table view". Purposeful whitespace, no decorative
illustrations, every pixel justifies its presence.

**Color direction:** Cool neutral base (slate/zinc grays) with a single sharp accent color —
indigo-500 for active/selected states. No warm tones except amber for warnings (e.g., "API key
missing"). Dark mode not required in this sprint but the palette should not fight it.

**Reference style:** Linear's engine selector cards adapted to a lighter background.
Stripe Docs' settings form aesthetic for the API key panel.

**Anti-patterns:**
- No gradient backgrounds behind cards
- No rounded-2xl "bubbly" cards — prefer rounded-lg or rounded-md
- No hero banners, taglines, or marketing copy anywhere in the upload flow
- Do not use the default Tailwind blue for the selected-engine accent; use indigo
- Do not show a spinner overlay on the entire page during upload — only the upload button/zone reacts

**Key UX moments deserving extra polish:**
1. **Engine selector card selection** — the transition from unselected to selected should be immediate (no animation delay), with a left-border accent (4 px solid indigo-500) and a subtle background shift (indigo-50). The card should feel like a toggle switch, not a form field.
2. **Gemini locked state** — the locked card must clearly communicate "you need a key" without being alarming. Use a small lock icon (16 px), muted text color, and an inline "→ Settings" text link, not a blocking modal.
3. **Settings save feedback** — after `POST /api/settings/api-keys` succeeds, show a green "Saved" inline badge that auto-hides after 3 seconds, replacing the Save button label temporarily. No toast libraries required — inline state is sufficient.
4. **Engine pill on job cards** — the pill should be visually compact: 1–2 word label, xs text, neutral-700 on neutral-100 background for Docling; indigo-700 on indigo-50 for PaddleOCR; violet-700 on violet-50 for Gemini. This creates quick visual scanability across the job list.

## Tech Stack Decisions

- **PaddleOCR 3** is installed as `paddleocr>=3.0.0` in `requirements.txt`, marked as optional with a comment. The import is guarded so the app starts normally if PaddleOCR is absent — only jobs using that engine will fail with a clear error message.
- **Gemini SDK**: `google-generativeai>=0.8.0` added to `requirements.txt`, also optional-guarded. Uses `gemini-2.0-flash` model ID.
- **pypdfium2** is already installed transitively via docling; use it directly in both new parsers for page rendering — no additional PDF rendering dependency needed.
- **python-dotenv `set_key()`** is used for persisting the API key; `python-dotenv` is already in `requirements.txt`. The `.env` file is at `BASE_DIR / ".env"`.
- No new frontend dependencies required. Engine selector built with plain Tailwind + React state.

## Risks

- **PaddleOCR 3 install footprint**: PaddleOCR has heavy GPU/CPU deps (~1 GB). Mitigation: document as optional, import-guarded, and tested with a mock in CI.
- **Gemini rate limits on large PDFs**: page-by-page sequential calls may be slow for 100+ page documents. Mitigation: sequential with 0.5 s delay is acceptable for MVP; note a batch/async upgrade path in code comments.
- **`.env` write permission**: on some deployments the `.env` file or its directory may be read-only. Mitigation: `settings.py` catches `PermissionError` and returns HTTP 500 with a clear message suggesting manual configuration.
- **Schema drift between engines**: PaddleOCR and Gemini parsers may produce fewer element types (no `table`, no `section_header` without heuristics). Mitigation: downstream consumers (chunker, exporter) already handle the minimal `text`-only element set; no changes to those services are needed in these sprints.
- **SQLite column migration**: adding `engine` column requires a schema change. Mitigation: in dev, `create_tables()` auto-creates; document that a production migration is `ALTER TABLE jobs ADD COLUMN engine VARCHAR(20) DEFAULT 'docling'`.
