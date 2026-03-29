# Feature Spec: Side Panel UI Overhaul

## Overview

Replace the current two-page layout (HomePage with job list + separate JobDetailPage) with a single-page application shell featuring a collapsible left sidebar for document navigation and a main content area for document viewing. This eliminates page transitions, lets users switch between documents instantly, and makes better use of screen real estate.

---

## Current State

### Architecture
- **Two pages**: `HomePage` (upload zone + job list table) and `JobDetailPage` (metadata + split pane viewer)
- **Routing**: `react-router-dom` with `/` and `/jobs/:jobId` routes
- **Layout**: `Layout.tsx` wraps both pages with a top header bar
- **Viewer**: `SplitPaneViewer` splits 50/50 between `PdfPane` (left) and `OutputPane` (right, 6 tabs)
- **Components**: `UploadZone`, `JobList`, `JobStatusBadge`, `DownloadButtons`, `TocSidebar`, `PdfPane`, `OutputPane`, 6 tab components

### Pain Points
- Navigating from job list to job detail requires a full page transition
- The header + metadata section consumes significant vertical space, reducing viewer area
- No way to quickly compare or switch between parsed documents
- The job list table is wide but the data is simple; a compact sidebar list would suffice

---

## Feature Requirements

### Must-Have
- [ ] **Collapsible left sidebar** (~280px default width) containing:
  - App logo/title (compact)
  - Upload button (always visible at top of sidebar)
  - Scrollable document list with filename, status badge, and date
  - Active document highlighting
  - Delete action per document
- [ ] **Main content area** that fills remaining viewport width, containing:
  - Compact metadata bar (single row: filename, status, page/element/chunk counts, download buttons, reprocess)
  - Full-height `SplitPaneViewer` below the metadata bar
  - Processing spinner and error states when job is not yet completed
- [ ] **Sidebar toggle button** to collapse/expand the sidebar (hamburger icon or chevron)
- [ ] **Collapsed sidebar state**: shows only icons (upload icon, narrow document indicators) at ~48px width
- [ ] **URL sync**: selected job ID reflected in URL (`/jobs/:jobId`) for bookmarkability; bare `/` shows sidebar with no document selected
- [ ] **Empty state**: when no document is selected, main area shows a centered prompt ("Select a document or upload a PDF")
- [ ] **Keyboard shortcut**: `Ctrl+B` / `Cmd+B` to toggle sidebar
- [ ] **Responsive behavior**: on screens below 768px, sidebar overlays as a drawer instead of pushing content
- [ ] **Preserve all existing functionality**: upload, polling, reprocess, download (JSON/MD/text/chunks), all 6 output tabs, PDF viewer with page navigation

### Nice-to-Have
- [ ] Sidebar width resizable via drag handle
- [ ] Search/filter input in sidebar to filter documents by filename
- [ ] Sidebar document list shows a tiny progress indicator for pending/running jobs
- [ ] Smooth CSS transitions for sidebar collapse/expand (200ms ease)
- [ ] Remember sidebar collapsed state in `localStorage`

---

## Technical Design

### Data Models
No backend changes required. All API endpoints remain identical. This is a frontend-only overhaul.

### API Endpoints
No new endpoints. Existing endpoints used:
| Method | Path | Used By |
|--------|------|---------|
| GET | /api/jobs | Sidebar document list |
| GET | /api/jobs/:id | Selected document status polling |
| POST | /api/upload | Upload button in sidebar |
| DELETE | /api/jobs/:id | Delete from sidebar list |
| POST | /api/jobs/:id/reprocess | Reprocess button in metadata bar |
| GET | /api/jobs/:id/result | Output tabs |
| GET | /api/jobs/:id/pdf | PDF viewer |
| GET | /api/jobs/:id/chunks | Chunks tab |
| GET | /api/jobs/:id/toc | Structure tab |
| GET | /api/jobs/:id/elements | Structure tab |
| GET | /api/jobs/:id/structure | Analysis tab |
| GET | /api/jobs/:id/download/* | Download buttons |

### UI Layout

```
+--+----------------------------------------------+
|S | Main Content Area                             |
|I |                                               |
|D | [Metadata Bar: filename | status | counts |   |
|E |  downloads | reprocess]                       |
|B |                                               |
|A | +-------------------++-----------------------+|
|R | | PDF Viewer        || Output Tabs           ||
|  | |                   ||                       ||
|  | |                   || [MD|JSON|TXT|STR|CHK| ||
|  | |                   ||  ANL]                 ||
|  | |                   ||                       ||
|  | +-------------------++-----------------------+|
+--+----------------------------------------------+
```

**Sidebar (expanded, ~280px)**:
```
+---------------------------+
| [Logo] Veluga Parser  [<] |
|---------------------------|
| [+ Upload PDF]            |
|---------------------------|
| Documents                 |
|  report.pdf        ✓ 3/28|
|  > invoice_kr.pdf  ✓ 3/27|  <- active (highlighted)
|  analysis.pdf      ⏳ 3/27|
|  memo.pdf          ✗ 3/26|
|                           |
+---------------------------+
```

**Sidebar (collapsed, ~48px)**:
```
+----+
| [>]|
| [+]|
|----|
| R  |
| >I |  <- active indicator
| A  |
| M  |
+----+
```

### Component Changes

#### New Components
| Component | File | Responsibility |
|-----------|------|----------------|
| `AppShell` | `components/AppShell.tsx` | Top-level layout: sidebar + main area, manages sidebar state |
| `Sidebar` | `components/Sidebar.tsx` | Collapsible sidebar with logo, upload, document list |
| `SidebarDocList` | `components/SidebarDocList.tsx` | Scrollable list of documents with status, date, delete |
| `SidebarDocItem` | `components/SidebarDocItem.tsx` | Single document row in sidebar |
| `MetadataBar` | `components/MetadataBar.tsx` | Compact single-row metadata + download + reprocess |
| `MainContent` | `components/MainContent.tsx` | Selected document viewer area (metadata bar + split pane) |
| `EmptyState` | `components/EmptyState.tsx` | Centered prompt when no document selected |

#### Modified Components
| Component | Changes |
|-----------|---------|
| `Layout.tsx` | Replace with `AppShell` as the root layout (or refactor in-place) |
| `UploadZone.tsx` | Create a compact variant for sidebar use (smaller, no large icon) |
| `SplitPaneViewer.tsx` | Remove hardcoded `calc(100vh - 180px)` height; use `h-full` flex child |
| `main.tsx` | Update routing: single route with `AppShell`, jobId as optional param |

#### Removed/Deprecated
| Component | Reason |
|-----------|--------|
| `HomePage.tsx` | Functionality absorbed into sidebar + empty state |
| `JobDetailPage.tsx` | Functionality absorbed into `MainContent` |
| `JobList.tsx` | Replaced by `SidebarDocList` (compact format, no table) |

### State Management
- `AppShell` holds: `sidebarCollapsed: boolean`, `selectedJobId: string | null`
- `selectedJobId` syncs with URL via `useParams` + `useNavigate`
- Sidebar document list uses existing `listJobs` API with auto-refresh polling
- Selected document uses existing `useJobStatus` hook
- Sidebar collapsed state optionally persisted to `localStorage`

### Routing Changes
```typescript
// Before
{ path: '/', element: <Layout />, children: [
  { index: true, element: <HomePage /> },
  { path: 'jobs/:jobId', element: <JobDetailPage /> },
]}

// After
{ path: '/', element: <AppShell />, children: [
  { index: true, element: <MainContent /> },
  { path: 'jobs/:jobId', element: <MainContent /> },
]}
```

`MainContent` reads `jobId` from `useParams()`. If absent, renders `EmptyState`. If present, renders metadata bar + split pane viewer.

---

## Sprint Plan

### Sprint 5: Side Panel UI Overhaul (Frontend Restructure)

**Goal**: Replace the two-page layout with a sidebar-based single-page shell. All existing functionality preserved.

**Scope**:
1. Create `AppShell` component with sidebar + main content layout
2. Create `Sidebar` component (collapsible, logo, upload button, document list)
3. Create `SidebarDocList` and `SidebarDocItem` (compact document list with status, delete, active state)
4. Create compact upload variant for sidebar
5. Create `MetadataBar` (single-row: filename, status badge, page/element/chunk counts, downloads, reprocess)
6. Create `MainContent` component (reads jobId from URL, shows empty state or viewer)
7. Create `EmptyState` component
8. Update `SplitPaneViewer` to use flex-based height instead of hardcoded calc
9. Update `main.tsx` routing
10. Remove or archive `HomePage.tsx`, `JobDetailPage.tsx`, `JobList.tsx`
11. Sidebar collapse/expand with toggle button and `Ctrl+B` / `Cmd+B`
12. Responsive: sidebar becomes overlay drawer below 768px
13. CSS transitions for sidebar open/close (200ms)
14. Persist sidebar state in `localStorage`

**Success Criteria**:
- [ ] App loads with sidebar visible showing document list
- [ ] Clicking a document in sidebar loads it in main content area without page navigation
- [ ] Upload button in sidebar triggers file picker; after upload, new job appears in list and is auto-selected
- [ ] Sidebar collapse/expand works via button and keyboard shortcut
- [ ] All 6 output tabs render correctly for a completed job
- [ ] PDF viewer renders and page navigation works
- [ ] Download buttons (JSON, Markdown, Text, Chunks) work
- [ ] Reprocess button works
- [ ] Delete from sidebar removes document from list
- [ ] Empty state shown when no document selected
- [ ] URL reflects selected document (`/jobs/:jobId`)
- [ ] Direct navigation to `/jobs/:jobId` selects that document
- [ ] Responsive: below 768px sidebar is an overlay drawer
- [ ] `npm run build` succeeds with zero TypeScript errors
- [ ] `npm run lint` passes with zero warnings

**Files to create**:
- `src/frontend/src/components/AppShell.tsx`
- `src/frontend/src/components/Sidebar.tsx`
- `src/frontend/src/components/SidebarDocList.tsx`
- `src/frontend/src/components/SidebarDocItem.tsx`
- `src/frontend/src/components/MetadataBar.tsx`
- `src/frontend/src/components/MainContent.tsx`
- `src/frontend/src/components/EmptyState.tsx`

**Files to modify**:
- `src/frontend/src/main.tsx` (routing)
- `src/frontend/src/components/SplitPaneViewer.tsx` (height fix)
- `src/frontend/src/components/UploadZone.tsx` (add compact variant prop)

**Files to remove/archive**:
- `src/frontend/src/pages/HomePage.tsx`
- `src/frontend/src/pages/JobDetailPage.tsx`
- `src/frontend/src/components/Layout.tsx` (replaced by AppShell)
- `src/frontend/src/components/JobList.tsx` (replaced by SidebarDocList)

---

### Sprint 6: Playwright E2E Test Suite

**Goal**: Comprehensive Playwright E2E tests covering the new sidebar UI and all user flows.

**Scope**:
1. Install and configure Playwright in the frontend project
2. Create Playwright config (`playwright.config.ts`) with:
   - Base URL pointing to dev server
   - Chromium browser (single browser sufficient for E2E)
   - Screenshot on failure
   - Video recording on retry
3. Write E2E tests for all critical user flows:
   - **Sidebar navigation**: sidebar renders, document list loads, clicking selects document
   - **Sidebar collapse/expand**: toggle button works, keyboard shortcut works, state persists
   - **Upload flow**: upload button opens file picker, after upload job appears in sidebar
   - **Document viewer**: metadata bar shows correct data, PDF pane renders, output tabs switch
   - **Download buttons**: download links have correct hrefs
   - **Reprocess**: reprocess button triggers API call
   - **Delete**: delete with confirmation removes document from sidebar
   - **Empty state**: no document selected shows empty state prompt
   - **URL sync**: direct navigation to `/jobs/:id` loads correct document
   - **Responsive**: sidebar becomes drawer on narrow viewport
4. Add npm scripts for running Playwright tests
5. Ensure tests can run in CI (headless mode)

**Success Criteria**:
- [ ] `npx playwright install` completes (Chromium)
- [ ] `npx playwright test` runs and all tests pass
- [ ] Tests cover: sidebar render, document selection, collapse/expand, upload flow, tab switching, download links, delete, empty state, URL navigation, responsive drawer
- [ ] Test failures produce screenshots for debugging
- [ ] Tests run in under 60 seconds total
- [ ] No flaky tests (tests use proper `waitFor` / `expect` patterns, no arbitrary sleeps)

**Files to create**:
- `src/frontend/playwright.config.ts`
- `src/frontend/e2e/sidebar.spec.ts` (sidebar render, collapse, expand, keyboard shortcut)
- `src/frontend/e2e/document-viewer.spec.ts` (select document, metadata, tabs, PDF)
- `src/frontend/e2e/upload-delete.spec.ts` (upload flow, delete flow)
- `src/frontend/e2e/navigation.spec.ts` (URL sync, empty state, responsive)

**Files to modify**:
- `src/frontend/package.json` (add Playwright dev dependency, add `test:e2e` script)

---

## Risks & Dependencies

| Risk | Impact | Mitigation |
|------|--------|------------|
| `react-split` may not behave well when sidebar resizes the available width | Viewer layout breaks on toggle | Use CSS `transition` on sidebar width; `SplitPaneViewer` already uses `ResizeObserver` in `PdfPane` |
| Sidebar document list polling may conflict with `useJobStatus` polling for selected doc | Duplicate API calls | Sidebar polls `listJobs` (lightweight); selected doc polls `getJob` (single job). No conflict — different endpoints |
| Removing `HomePage` and `JobDetailPage` is a breaking change to existing bookmarks | Users with bookmarked `/` or `/jobs/:id` see errors | Both routes still exist in new routing; `/` shows sidebar + empty state, `/jobs/:id` shows sidebar + selected doc |
| Playwright tests need a running backend with test data | Tests fail in CI without backend | Use Playwright `route` API to mock all `/api/*` endpoints with fixture data; no real backend needed |
| `react-pdf` worker initialization may fail in Playwright | PDF tests flaky | Mock the PDF pane in E2E tests or skip PDF rendering assertions; focus on metadata and tab tests |
| Responsive overlay drawer needs click-outside-to-close and focus trap | Accessibility issues | Use `useEffect` with `mousedown` listener for click-outside; aria attributes for drawer |

## Tech Stack Decisions

- **No new runtime dependencies**: The sidebar is built with Tailwind CSS utility classes and existing React primitives
- **Playwright** (not Cypress) for E2E tests as specified in project conventions
- **API mocking in Playwright**: Use `page.route()` to intercept API calls with fixture JSON, keeping tests fast and deterministic
- **No state management library**: `useState` + URL params + context (if needed) is sufficient for sidebar state
- **localStorage** for sidebar collapsed preference only
