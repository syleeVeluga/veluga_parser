# Spec: Split-Pane Comparison Viewer (Sprint 5)

## Feature Overview
A drag-resizable split view on `JobDetailPage` for completed jobs:
- **Left pane** — original PDF rendered inline via `<iframe>` pointing to `GET /api/jobs/{job_id}/pdf`
- **Right pane** — tabbed output viewer: Markdown (rendered HTML), JSON (syntax-highlighted), Plain Text, Structured (existing ResultsViewer)
- Drag divider to resize panes; each pane scrolls independently

## What Already Exists vs. What Must Be Added

### Already Exists
- `JobDetailPage` with metadata + DownloadButtons
- `ResultsViewer` — page-by-page structured viewer (Sprint 4)
- `GET /api/jobs/{id}/download/markdown`, `/download/text`, `/download/json`, `/images/{filename}`
- `getDownloadUrl`, `getImageUrl`, `getResult` in api.ts
- Original PDF stored at `uploads/{job_id}/input.pdf` — no HTTP serving yet
- Vite proxy `/api` → `http://localhost:8000`

### Must Be Added
| Item | Type |
|---|---|
| `GET /api/jobs/{job_id}/pdf` | New backend route |
| `getPdfUrl(jobId)` | api.ts helper |
| `SplitPaneViewer.tsx` | New component |
| `PdfPane.tsx` | New component |
| `OutputPane.tsx` | New component |
| `tabs/MarkdownTab.tsx` | New component |
| `tabs/JsonTab.tsx` | New component |
| `tabs/PlainTextTab.tsx` | New component |
| `tabs/StructuredTab.tsx` | New component (wraps ResultsViewer) |
| `react-split`, `react-markdown`, `remark-gfm`, `react-syntax-highlighter` | npm deps |

---

## Sprint 5: Split-Pane Comparison Viewer

### Backend
- Add `GET /api/jobs/{job_id}/pdf` to `results.py` — serves `job.file_path` as `application/pdf` via `FileResponse`. Job must exist and be `completed`. Returns 404 if file missing.

### Frontend
- `api.ts`: add `getPdfUrl(jobId: string): string` → `/api/jobs/${jobId}/pdf`
- `SplitPaneViewer.tsx`: `<Split minSize={300} defaultSizes={[50,50]} gutterSize={8}>` wrapping `PdfPane` + `OutputPane`. Container: `height: calc(100vh - 180px)`, `overflow: hidden`, full-width.
- `PdfPane.tsx`: `<iframe src={getPdfUrl(jobId)} className="w-full h-full border-0" title="Original PDF">` with fallback text.
- `OutputPane.tsx`: tab bar (Markdown / JSON / Text / Structured) + tab content area (`flex-1 overflow-y-auto`).
- `tabs/MarkdownTab.tsx`: fetch `/api/jobs/{jobId}/download/markdown` as text → `<ReactMarkdown remarkPlugins={[remarkGfm]}>`.
- `tabs/JsonTab.tsx`: `getResult(jobId)` → `JSON.stringify(data, null, 2)` → `<SyntaxHighlighter language="json">`.
- `tabs/PlainTextTab.tsx`: fetch `/api/jobs/{jobId}/download/text` as text → `<pre>`.
- `tabs/StructuredTab.tsx`: wraps `<ResultsViewer jobId={jobId} filename={filename} status="completed" />`.
- `JobDetailPage.tsx`: replace `ResultsViewer` block with `<SplitPaneViewer jobId={jobId} filename={job.filename} />`. Move split pane outside the `max-w-5xl` container for full width.

### Success Criteria
- [ ] SC-1: `GET /api/jobs/{job_id}/pdf` → HTTP 200 + `Content-Type: application/pdf`
- [ ] SC-2: `GET /api/jobs/nonexistent/pdf` → HTTP 404
- [ ] SC-3: PDF file missing on disk → HTTP 404
- [ ] SC-4: Browser renders PDF inline in left pane
- [ ] SC-5: Dragging divider resizes both panes
- [ ] SC-6: Neither pane collapses below 300px
- [ ] SC-7: Both panes scroll independently
- [ ] SC-8: "Markdown" tab renders formatted HTML (not raw `##`)
- [ ] SC-9: "JSON" tab shows syntax-colored JSON
- [ ] SC-10: "Text" tab shows plain text in monospace
- [ ] SC-11: "Structured" tab shows existing page-by-page viewer
- [ ] SC-12: Tab state preserved when dragging divider
- [ ] SC-13: Loading state shown during fetch
- [ ] SC-14: Error shown if fetch fails
- [ ] SC-15: `npm run build` exits 0, 0 TS errors
- [ ] SC-16: `pytest` exits 0

### Out-of-Scope
- PDF/structured viewer page synchronization
- Mobile responsive layout
- Persisting split ratio in localStorage
- `@tailwindcss/typography` plugin (prose styling done inline)
- Frontend unit tests
