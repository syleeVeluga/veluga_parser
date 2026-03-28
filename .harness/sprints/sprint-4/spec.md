# Feature Spec: Output Viewer Enhancement

## Overview
Enhance the existing `ResultsViewer` component and add a backend image-serving endpoint so users can view all extracted content — text, tables, and actual images — from parsed PDFs in a fully integrated output viewer on the `JobDetailPage`. The viewer already handles page navigation and text/table rendering; this sprint completes image display and polishes the metadata panel and navigation UX.

## Feature Requirements

### Must-Have
- [ ] Backend endpoint `GET /api/jobs/{job_id}/images/{filename}` that serves extracted image files from `uploads/{job_id}/images/`
- [ ] `ImageElement` component renders an actual `<img>` tag using the new endpoint URL (not just placeholder text)
- [ ] Metadata summary panel within the viewer: document title (filename), total pages, parse status, detected languages, has_tables flag, has_images flag
- [ ] Page navigation: Previous / Next buttons in addition to the sidebar list
- [ ] Scroll-to-top of content area on page change
- [ ] Element-count hint per page in sidebar (e.g. "Page 1 · 4 items")
- [ ] Fix: Replace `alert()` in `UploadZone` with inline error state
- [ ] Fix: Stabilize `key` props in `ResultsViewer` table rendering (use content-based keys, not array indices)
- [ ] Fix: `useJobStatus` — stop polling after 3 consecutive errors

### Nice-to-Have
- [ ] Image lightbox/modal on click
- [ ] Filter toggle per element type
- [ ] React Testing Library tests

---

## Technical Design

### What Already Exists

| Item | File | State |
|------|------|-------|
| Page navigator sidebar | `ResultsViewer.tsx` | Exists, needs UX polish |
| `TextElement` renderer | `ResultsViewer.tsx` | Complete |
| `TableElement` renderer | `ResultsViewer.tsx` | Complete (key bug to fix) |
| `ImageElement` renderer | `ResultsViewer.tsx` | Placeholder only — no `<img>` |
| `GET /api/jobs/{id}/result` | `routes/results.py` | Complete — returns pages + metadata |
| Image files on disk | `uploads/{job_id}/images/*.png` | Exist — no HTTP serving endpoint |
| Metadata display | `JobDetailPage.tsx` | Exists above viewer — not inside viewer |
| `useJobStatus` polling | `hooks/useJobStatus.ts` | No back-off on error |
| `UploadZone` validation | `components/UploadZone.tsx` | Uses `alert()` |

### API Endpoints

#### New Endpoint

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/jobs/{job_id}/images/{filename}` | Serve an extracted image file. Returns 404 if not found. |

**Security:** Validate `filename` contains no path separators (`/`, `\`, `..`). Confirm resolved path is inside the image directory.

#### Image URL Construction (Frontend)

Add `getImageUrl(jobId: string, filename: string): string` to `api.ts`.

In `ImageElement`: extract basename from `path` field, build URL as `/api/jobs/{jobId}/images/{filename}`.

### Component Architecture

#### Modified: `ResultsViewer.tsx`

```
ResultsViewer
├── ViewerMetadataPanel         ← NEW
├── PageSidebar                 ← ENHANCED: element-count hint per page
├── PageNavigationControls      ← NEW: Prev / Next buttons + "Page X of N"
└── PageContentArea             ← ENHANCED: scroll-to-top on page change
    └── PageContent
        ├── TextElement          (unchanged)
        ├── TableElement         (key prop fix)
        └── ImageElement         ← ENHANCED: renders <img>
```

**Updated `ResultsViewer` props:**
```typescript
interface ResultsViewerProps {
  jobId: string
  filename: string   // NEW — for metadata panel
  status: string     // NEW — for metadata panel
}
```

---

## Sprint Plan

### Sprint 4: Output Viewer — Image Serving + Viewer Enhancements + Bug Fixes

**Goal:** Complete the output viewer so extracted images render in the browser, add a metadata summary panel inside the viewer, improve page navigation UX, and fix the three known bugs from Sprint 3.

**Backend changes:**
- Add `GET /api/jobs/{job_id}/images/{filename}` to `src/backend/routes/results.py`
- Add `getImageUrl(jobId, filename)` helper to `src/frontend/src/services/api.ts`

**Frontend changes:**
- `ResultsViewer.tsx`: `ViewerMetadataPanel`, `ImageElement` with `<img>`, `PageNavigationControls`, element-count hints, scroll-to-top, key prop fixes
- `JobDetailPage.tsx`: pass `filename` and `status` props to `<ResultsViewer>`
- `UploadZone.tsx`: replace `alert()` with inline error state
- `useJobStatus.ts`: add consecutive error counter; clear interval after 3 errors

**Success Criteria:**
- [ ] `GET /api/jobs/{job_id}/images/{filename}` returns HTTP 200 with `Content-Type: image/png` for a valid file
- [ ] `GET /api/jobs/{job_id}/images/../secrets.txt` returns HTTP 400 (path traversal blocked)
- [ ] `GET /api/jobs/{job_id}/images/nonexistent.png` returns HTTP 404
- [ ] `<img>` elements with actual image content render in the browser for completed jobs with images
- [ ] `ViewerMetadataPanel` renders filename, total pages, status badge, languages, table/image tags
- [ ] Prev/Next buttons work and scroll content area to top
- [ ] Sidebar items show element count hint
- [ ] Non-PDF upload shows inline error (not `window.alert`)
- [ ] `useJobStatus` stops polling after 3 consecutive errors
- [ ] `npm run build` succeeds with 0 TypeScript errors
- [ ] `pytest` exit code 0

**Out-of-Scope:**
- Image lightbox/modal
- Filter toggles
- Frontend unit tests
- Batch upload / search
