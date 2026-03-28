# Evaluation Report - Sprint 4

## Overall Result: PASS

## Scores
| Category | Score (0-100) | Weight | Weighted Score |
|----------|--------------|--------|---------------|
| Functionality | 95 | 30% | 28.5 |
| Code Quality | 92 | 25% | 23.0 |
| Testing | 90 | 20% | 18.0 |
| Security | 95 | 15% | 14.25 |
| UI/UX | 90 | 10% | 9.0 |
| **Total** | | | **92.75** |

---

## Contract Item Results

1. [PASS] `GET /api/jobs/{job_id}/images/{filename}` endpoint exists and is registered — `results.py` line 102 defines `@router.get("/jobs/{job_id}/images/{filename}")`. `main.py` line 44 includes `results_router` under `/api`, so the full path `/api/jobs/{job_id}/images/{filename}` is active.

2. [PASS] Path traversal protection via `filename != Path(filename).name` check — `results.py` line 105: `if filename != Path(filename).name or "/" in filename or "\\" in filename:` raises HTTP 400. A secondary `resolve().relative_to()` check on lines 114-117 provides a second layer of protection. Both verified by reading the file.

3. [PASS] `GET /api/jobs/{job_id}/images/nonexistent.png` returns 404 — `results.py` lines 118-119: `if not image_path.exists(): raise HTTPException(status_code=404, detail="Image not found")`. Logic confirmed.

4. [PASS] `ImageElement` renders an `<img>` tag — `ResultsViewer.tsx` lines 91-96: `<img src={getImageUrl(jobId, filename)} alt={filename} ... onError={() => setImgError(true)} />`. Falls back to a text placeholder on load error.

5. [PASS] `ViewerMetadataPanel` exists and renders filename, total_pages, status badge, languages, has_tables/has_images — `ResultsViewer.tsx` lines 114-156. All six data points rendered: filename (line 133), `total_pages` with plural suffix (line 137), color-coded status badge (lines 123-139), languages joined by comma (lines 141-143), `Tables` badge when `has_tables` (lines 144-148), `Images` badge when `has_images` (lines 149-152).

6. [PASS] Prev/Next navigation buttons exist — `ResultsViewer.tsx` lines 228-244: `← Prev` button (disabled when `currentIndex <= 0`) and `Next →` button (disabled when `currentIndex >= totalPages - 1`), with a "Page X of Y" label between them.

7. [PASS] Scroll-to-top on page change — `ResultsViewer.tsx` line 165: `const contentRef = useRef<HTMLDivElement>(null)`. The `goToPage` function (lines 182-185) sets `contentRef.current.scrollTop = 0`. `ref={contentRef}` is attached to the scrollable content `<div>` at line 249.

8. [PASS] Element-count hints in sidebar — `ResultsViewer.tsx` lines 214-217: each sidebar button renders `{p.elements.length} item{p.elements.length !== 1 ? 's' : ''}` as a secondary label beneath "Page N".

9. [PASS] No `alert()` in `UploadZone.tsx` — grep for `alert(` in `UploadZone.tsx` returned zero matches. Validation errors are surfaced via `validationError` state rendered inline as a `<p role="alert">` at line 66.

10. [PASS] `useJobStatus.ts` stops polling after 3 consecutive errors — `useJobStatus.ts` lines 38-45: `errorCountRef.current += 1` on each error; `if (errorCountRef.current >= 3 && intervalRef.current)` calls `clearInterval`. Counter is reset to 0 on any successful fetch (line 27).

11. [PASS] `npm run build` passes — `tsc && vite build` succeeded with zero TypeScript errors; 41 modules transformed, built in 1.45s. No warnings.

12. [PASS] `pytest` passes — 42 tests collected, 42 passed in 1.33s. Zero failures.

13. [PASS] `ResultsViewer` accepts `filename` and `status` props — `ResultsViewer.tsx` lines 10-14: `interface ResultsViewerProps { jobId: string; filename: string; status: string }`. Component exported on line 160: `export function ResultsViewer({ jobId, filename, status }: ResultsViewerProps)`.

14. [PASS] `JobDetailPage.tsx` passes `filename` and `status` to `<ResultsViewer>` — `JobDetailPage.tsx` line 87: `<ResultsViewer jobId={jobId} filename={job.filename} status={job.status} />`.

15. [PASS] `getImageUrl` exists in `api.ts` — `api.ts` lines 98-100: exported function `getImageUrl(jobId: string, filename: string): string` returning `/api/jobs/${jobId}/images/${encodeURIComponent(filename)}`. Filename is URL-encoded, preventing issues with spaces and special characters.

---

## Bugs Found

### Critical
None.

### High
None.

### Medium
None.

### Low
- **`ResultsViewer.tsx` key props use array index** (lines 105-107): `key={\`text-${i}\`}`, `key={\`table-${i}\`}`, `key={\`img-${i}\`}`. Acceptable since elements within a page are never reordered at runtime, but fragile if element ordering changes in future.
- **`useJobStatus.ts` potential double-fetch on startup** (lines 51-52): `fetchJob()` is called immediately, then `setInterval(fetchJob, 2000)` starts. If the first call's promise takes more than 2 seconds, a second call will fire before the first resolves. Low practical impact (idempotent GET), but could cause a flicker if the second call resolves before the first.
- **`get_image` does not reuse `_get_result_or_404`** (`results.py` lines 108-110): A manual inline query for `ParsedResult` is performed instead of calling the shared helper. Not a bug but reduces consistency with the rest of the module.

---

## Detailed Code Review

### What Went Well
- Double-layered path traversal protection in `get_image`: filename-equality guard PLUS `resolve().relative_to()` check. Robust against edge cases on both Windows and Unix path separators.
- `getImageUrl` applies `encodeURIComponent` to filename, preventing malformed URLs for files with spaces or non-ASCII names.
- `ImageElement` has an `onError` fallback, so a missing image file on the server produces a graceful UI placeholder rather than a broken `<img>` tag.
- `useJobStatus` correctly resets `errorCountRef` to 0 on success, ensuring transient errors do not cause premature polling termination.
- `UploadZone.tsx` clears the file input value after both successful upload and validation failure, preventing stale state on re-select attempts.
- All six modified files are well within the 300-line limit (max 262 lines for `ResultsViewer.tsx`). Zero TypeScript `any` types across all frontend files.
- The Sprint 3 recommended fix for `useJobStatus` (stop polling on consecutive errors) was fully implemented as `errorCountRef >= 3`.
- The Sprint 3 recommended fix replacing `alert()` in `UploadZone` with inline state was fully implemented.

### Needs Improvement
- File: `src/backend/routes/results.py`, Lines 108-110
  - Issue: Inline `ParsedResult` query duplicates logic instead of using `_get_result_or_404`.
  - Suggestion: Either call `_get_result_or_404` or add a dedicated `_get_image_dir_or_404` helper for consistency.
- File: `src/frontend/src/components/ResultsViewer.tsx`, Lines 104-108
  - Issue: Index-based `key` props.
  - Suggestion: If the backend ever adds a stable `id` field to `ResultElement`, prefer that over the array index.

---

## Required Fixes for FAIL (in priority order)
N/A — Sprint 4 passes with a weighted score of 92.75, all categories above 50%, and zero critical bugs.

Overall Result: PASS
