# Sprint 3 Contract: Frontend Web UI

## Sprint Goal
React 18 + Vite + TailwindCSS frontend with PDF upload, job list, real-time status polling, results viewer, and download buttons. FastAPI serves the built frontend as static files.

## Implementation Goals
1. Vite + React 18 + TailwindCSS + React Router v6 scaffold in `src/frontend/`
2. `services/api.ts` — typed fetch wrappers for all backend endpoints
3. `HomePage` (`/`) — UploadZone + JobList with auto-refresh
4. `JobDetailPage` (`/jobs/:id`) — polling, status badge, metadata, DownloadButtons, ResultsViewer
5. `useUpload` hook — upload state machine (idle/uploading/error)
6. `useJobStatus` hook — polling with cleanup on unmount
7. `JobStatusBadge` component — color-coded status
8. FastAPI `StaticFiles` mount for production frontend serving
9. `npm run build` succeeds with no TypeScript errors

## Testable Success Criteria
- [ ] `npm run build` in `src/frontend/` succeeds (exit code 0, no TS errors)
- [ ] `npm run lint` passes (no ESLint errors)
- [ ] HomePage renders UploadZone and JobList
- [ ] UploadZone validates PDF MIME type client-side and rejects non-PDF
- [ ] JobList shows job status badges with correct color per status
- [ ] JobDetailPage polls `GET /api/jobs/:id` every 2 seconds while pending/running
- [ ] DownloadButtons are disabled until status=completed
- [ ] ResultsViewer renders text elements and tables from result JSON
- [ ] FastAPI serves frontend from `src/frontend/dist/` at root `/`
- [ ] No TypeScript `any` types used (per CLAUDE.md convention)

## Out-of-Scope for This Sprint
- Playwright E2E tests (heavy setup, nice-to-have)
- Drag-and-drop (nice-to-have)
- Search within results (nice-to-have)

## Technical Decisions
- TailwindCSS v3 (stable, well-supported with Vite)
- React Router v6 with `createBrowserRouter`
- Native `fetch` API (no axios)
- Poll interval: 2 seconds for job detail, 5 seconds for job list
- Backend API base URL: `http://localhost:8000` in dev (proxied via Vite), relative in prod
- TypeScript strict mode enabled
- File structure: components/, pages/, hooks/, services/ under `src/frontend/src/`
