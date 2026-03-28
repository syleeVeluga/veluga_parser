# Final Report: Split-Pane Comparison Viewer (Sprint 5)

**Date:** 2026-03-29
**Sprint:** 5
**Result:** PASS (18/18 criteria)

## Implemented Features

### Backend
- `GET /api/jobs/{job_id}/pdf` — serves the original uploaded PDF via `FileResponse(media_type="application/pdf")`. Validates job existence, completed status, and file presence on disk.

### Frontend — New Components

**`SplitPaneViewer.tsx`**
- `react-split` drag-resizable layout; `minSize={300}`, `sizes=[50,50]`, `gutterSize=8`
- Full-height flex layout fills viewport below header/metadata bar

**`PdfPane.tsx`**
- `<iframe src={getPdfUrl(jobId)}>` for inline PDF rendering
- Fallback text for browsers without a built-in PDF viewer

**`OutputPane.tsx`**
- Tab bar: Markdown | JSON | Text | Structured
- Tab state is local `useState`, preserved across divider drags
- Each tab content area has independent `overflow-y-auto` scroll

**`tabs/MarkdownTab.tsx`**
- Fetches `/api/jobs/{jobId}/download/markdown` as text
- Renders with `react-markdown` + `remark-gfm` for tables/GFM
- Custom component overrides for all HTML elements (h1–h3, p, ul, table, code, etc.)

**`tabs/JsonTab.tsx`**
- Calls `getResult(jobId)` → `JSON.stringify` with 2-space indent
- Syntax-highlighted with `react-syntax-highlighter` (atomOneDark theme, line numbers)

**`tabs/PlainTextTab.tsx`**
- Fetches `/api/jobs/{jobId}/download/text` as text
- Renders in `<pre className="whitespace-pre-wrap font-mono">`

**`tabs/StructuredTab.tsx`**
- Thin wrapper around existing `ResultsViewer` (page-by-page viewer from Sprint 4)

### Supporting Changes
- `api.ts`: `getPdfUrl(jobId)` helper
- `JobDetailPage.tsx`: refactored to full-height flex; renders `<SplitPaneViewer>` for completed jobs
- npm deps added: `react-split`, `react-markdown`, `remark-gfm`, `react-syntax-highlighter`, `@types/react-syntax-highlighter`

## Test Results
- `pytest`: 42/42 passed
- `npm run build`: 0 TypeScript errors, 1173 modules transformed

## Known Limitations
- PDF/structured viewer page sync not implemented (out of scope)
- No mobile/responsive fallback for split pane (desktop-only)
- Split ratio not persisted across page refreshes

## Files Changed
- `src/backend/routes/results.py`
- `src/frontend/src/services/api.ts`
- `src/frontend/src/pages/JobDetailPage.tsx`
- `src/frontend/src/components/SplitPaneViewer.tsx` (new)
- `src/frontend/src/components/PdfPane.tsx` (new)
- `src/frontend/src/components/OutputPane.tsx` (new)
- `src/frontend/src/components/tabs/MarkdownTab.tsx` (new)
- `src/frontend/src/components/tabs/JsonTab.tsx` (new)
- `src/frontend/src/components/tabs/PlainTextTab.tsx` (new)
- `src/frontend/src/components/tabs/StructuredTab.tsx` (new)
