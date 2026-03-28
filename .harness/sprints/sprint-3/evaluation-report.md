# Evaluation Report - Sprint 3

## Overall Result: PASS

## Scores
| Category | Score (0-100) | Weight | Weighted Score |
|----------|--------------|--------|---------------|
| Functionality | 88 | 30% | 26.4 |
| Code Quality | 80 | 25% | 20.0 |
| Testing | 90 | 20% | 18.0 |
| Security | 85 | 15% | 12.75 |
| UI/UX | 90 | 10% | 9.0 |
| **Total** | | | **86.15** |

---

## Contract Item Results

- [PASS] `npm run build` succeeds (exit code 0, no TS errors): `tsc && vite build` completed in 1.37 s, 41 modules, no TypeScript errors.
- [PASS] `npm run lint` passes (0 errors/warnings): ESLint exits 0 with `--max-warnings 0`. One `react-hooks/exhaustive-deps` warning in `JobList.tsx` is suppressed via `// eslint-disable-line`; the tool reports clean, but the suppression hides a real logic bug (see Bugs section).
- [PASS] UploadZone validates PDF MIME type and rejects non-PDF: `file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')` check on line 14 of `UploadZone.tsx`; non-PDF triggers `alert()` and resets the input.
- [PASS] JobList has auto-refresh logic for active jobs: `setInterval(() => fetchJobs(page), 5000)` wired in `useEffect`; interval is started when `hasActive` is true. NOTE: the implementation has a stale-state bug on first render (see High bug).
- [PASS] JobDetailPage polls every 2 seconds while pending/running: `useJobStatus` hook uses `POLL_INTERVAL_MS = 2000`; polling stops on terminal status via `clearInterval` inside the fetch callback.
- [PASS] DownloadButtons disabled until status=completed: `enabled={job?.status === 'completed'}` in `JobDetailPage.tsx`; when `enabled=false`, `<a>` has `pointer-events-none`, `cursor-not-allowed`, and `href={undefined}`.
- [PASS] ResultsViewer renders text, table, and image elements: `TextElement`, `TableElement`, `ImageElement` sub-components all implemented; `PageContent` dispatches on `elem.type`.
- [PASS] FastAPI StaticFiles mount in `main.py`: `app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")` present on line 49; conditionally mounted only when `dist/` exists, which is correct for production.
- [PASS] No TypeScript `any` types used: grep across all `.ts/.tsx` files returns zero matches for `: any`, `<any>`, or `as any`. ESLint rule `@typescript-eslint/no-explicit-any: 'error'` is enforced and passes.

---

## Bugs Found

### Critical
None.

### High
- **JobList auto-refresh broken on initial page load** (`src/frontend/src/components/JobList.tsx`, line 32–38): The `useEffect` reads the `items` state to compute `hasActive` **before** `fetchJobs(page)` resolves. On first render `items` is `[]`, so `hasActive` is always `false` and the interval is never started. Jobs in pending/running state when the user lands on the home page will not auto-refresh. The developer suppressed the resulting `react-hooks/exhaustive-deps` ESLint warning with `// eslint-disable-line react-hooks/exhaustive-deps` rather than fixing the dependency. This means the `npm run lint` report is clean but the underlying logic defect persists.

### Medium
- **`useJobStatus` continues polling on API error** (`src/frontend/src/hooks/useJobStatus.ts`): When the backend is offline the `catch` block sets the error state but does not clear the interval. The hook keeps firing `getJob()` every 2 seconds indefinitely with no back-off or retry cap.
- **`DownloadButtons` uses `aria-disabled` on `<a>` without `role="button"`** (`src/frontend/src/components/DownloadButtons.tsx`): `aria-disabled` applies to interactive roles; a bare `<a>` without `href` may not announce the disabled state correctly in some screen readers.
- **`ResultsViewer` uses array index as React `key`** (`src/frontend/src/components/ResultsViewer.tsx`, lines 28, 36, 38): `key={i}`, `key={ri}`, `key={ci}` on table rows/cells. Reordered elements would cause incorrect reconciliation.

### Low
- **`UploadZone` uses `alert()` for MIME validation feedback** (`UploadZone.tsx` line 15): Blocking modal breaks UI testing and accessibility. The component already supports an inline `role="alert"` error paragraph; MIME rejection should use that instead.
- **`ResultsViewer` re-fetches on every mount**: No caching; navigating away and back to a completed job triggers a full API call each time. Acceptable for MVP but will feel slow on large results.
- **No loading skeleton on `JobDetailPage`**: The loading state renders a plain `<p>` causing layout shift when job data arrives.

---

## Detailed Code Review

### What Went Well

1. **TypeScript strictness fully honoured**: `strict: true` plus `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch` in `tsconfig.json`. Zero `any` types across all files. All API response shapes fully typed with exported interfaces.

2. **`useJobStatus` hook cleanup is correct**: The `cancelled` flag prevents state updates on unmounted components. `intervalRef` typed as `ReturnType<typeof setInterval>` works correctly in both browser and Node environments. The cleanup function reliably clears the interval and nulls the ref.

3. **`useUpload` state machine is clean**: Three-state model (`idle | uploading | error`). Error messages extracted safely with `instanceof Error`. `reset()` exposed for consumers.

4. **`api.ts` is well-typed with zero `any`**: Generic `apiFetch<T>` centralises error handling. `apiFetch<unknown>` used correctly for the `DELETE` call. `getDownloadUrl` returns a plain string enabling the `<a download>` pattern cleanly.

5. **`ResultsViewer` covers all three element types**: Table rendering correctly uses `rows[0]` as the header. Falls back to `<pre>` if `rows` is absent.

6. **FastAPI `StaticFiles` mount is production-correct**: Conditional on `dist/` existence prevents dev-mode startup crash. Mount placed after all API routers so `/api` routes take precedence over the SPA catch-all.

7. **Backend regression-free**: All 42 backend tests pass without modification.

8. **Clean production build**: 41 modules, JS bundle 223 kB (72 kB gzipped), CSS 11.8 kB (3.1 kB gzipped). TypeScript compilation zero errors.

9. **Accessibility basics present**: `UploadZone` has `role="button"` and `aria-label`. Error paragraphs use `role="alert"`. File input has `aria-label`. Job detail error message uses `role="alert"`.

10. **Color-coded status badges**: All four statuses mapped to distinct Tailwind color classes (gray / yellow-pulse / green / red) with safe fallback for unknown values.

11. **`JobDetailPage` component split**: Outer `JobDetailPage` handles the `useParams` guard and early `<Navigate>` redirect cleanly; inner `JobDetail` holds all hook and rendering logic, avoiding conditional hook issues.

### Needs Improvement

1. **JobList polling logic** (see High bug): The `hasActive` check must run on the *fetched* data, not the pre-fetch stale `items` state. The `eslint-disable-line` comment is a code smell that masked the logic error.

2. **No error-driven polling back-off in `useJobStatus`**: Stop or slow the interval after consecutive errors to avoid hammering a down backend.

3. **No frontend unit/component tests**: No React Testing Library tests exist for any hook or component. Hook behaviour (especially `useJobStatus` cleanup and interval stop) and `UploadZone` MIME rejection are untested. Backend test coverage is excellent (42/42) but frontend has zero.

4. **Replace `alert()` in `UploadZone`** with the existing inline error state for consistent, non-blocking, accessible feedback.

---

## Required Fixes for FAIL (in priority order)

Sprint 3 PASSES (weighted score 86.15, all categories >= 50%, zero critical bugs). The following fixes are strongly recommended before Sprint 4 begins:

1. **(High — fix before next sprint)** Fix `JobList` auto-refresh stale-state bug. Remove the `eslint-disable-line` suppression. Rework the effect so the interval is set up based on freshly-fetched data, for example by moving the active-check inside the interval callback or by adding `items` to the dependency array and re-evaluating the interval on each fetch cycle.

2. **(Medium)** Add polling back-off to `useJobStatus`: clear or pause the interval after 3–5 consecutive `catch` errors.

3. **(Medium)** Replace `alert()` in `UploadZone` with inline error state.

4. **(Low)** Stabilise `key` props in `ResultsViewer` table rendering.

5. **(Future sprint)** Add React Testing Library tests for `useJobStatus` (interval setup, cleanup, terminal-status stop) and `UploadZone` (MIME rejection path).
