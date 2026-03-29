# Sprint 3 Contract: Engine Selector UI + Upload Integration

## Goal
Users can choose the extraction engine before uploading a PDF. Gemini option gated by API key availability. Engine shown on job cards.

## Implementation Goals
1. `EngineSelector.tsx` component — three option cards (Docling, PaddleOCR 3, Gemini Flash) with radio semantics
2. Wire `EngineSelector` into `Sidebar.tsx` upload flow — selected engine passed to `uploadPdf()`
3. Update `uploadPdf()` in `api.ts` to accept optional `engine` parameter
4. `useUpload.ts` hook updated to accept and pass engine
5. Fetch `gemini_configured` in Sidebar on mount — disable Gemini option if not configured
6. Gemini card shows lock icon + "→ Settings" link when not configured
7. Playwright E2E tests: engine selector renders, Gemini locked state, PaddleOCR selection

## Success Criteria (each independently testable)
- `EngineSelector` renders three cards with correct labels ("Docling", "PaddleOCR 3", "Gemini Flash")
- Clicking "PaddleOCR 3" makes it visually selected (data-engine attribute or aria-checked)
- Gemini card has `aria-disabled="true"` when `gemini_configured` is false
- Selecting PaddleOCR engine then uploading results in a job with `engine: "paddleocr"` in the API response
- All existing Playwright specs continue to pass
- `npm run build` exits 0

## Out of Scope
- Per-engine advanced options
- PaddleOCR language hint UI
- Batch/async Gemini upload

## Technical Decisions
- EngineSelector is self-contained; state lifted to Sidebar (selected engine)
- `useUpload` hook accepts `engine` parameter and passes to `uploadPdf()`
- `uploadPdf()` appends engine to FormData
- `getApiKeyStatus()` called once on Sidebar mount; result cached in state
- Gemini lock state: card opacity-50 + `aria-disabled="true"` + lock icon + "→ Settings" Link
- Selected card: 4px left border indigo-500, indigo-50 background
