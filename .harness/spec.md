# Feature Spec: Sprint 8 — Markdown Viewer E2E Tests + Helper Mocks

## Overview
Sprint 7 shipped per-page Markdown pagination and a new MarkdownTab component, but left two
medium-severity testing gaps identified in the evaluation report: no Playwright spec for the
Markdown viewer and no route mocks for the new `/markdown/pages` endpoints in `helpers.ts`.
This Sprint closes those gaps by adding `markdown-viewer.spec.ts` and patching `helpers.ts`
with the missing mocks and mock fixtures.

## Feature Requirements

### Must-Have
- [ ] Add mock for `GET /api/jobs/*/markdown/pages` in `helpers.ts` returning a multi-page
      `MarkdownPagesResponse` (job_id, total_pages, pages array)
- [ ] Add mock for `GET /api/jobs/*/markdown/pages/*` in `helpers.ts` returning per-page
      `MarkdownPageResponse` (job_id, page_number, total_pages, content)
- [ ] Add `MOCK_MARKDOWN_PAGES` and `MOCK_MARKDOWN_PAGE_*` fixtures to `fixtures.ts`
- [ ] Create `src/frontend/e2e/markdown-viewer.spec.ts` with the following test cases:
  - Prev button is disabled on page 1
  - Next button is enabled on page 1 (not last page)
  - Clicking Next advances the page indicator from "1 / 3" to "2 / 3"
  - Page content changes after navigation (different text visible)
  - Next button is disabled on the last page
  - Prev button re-enables after advancing past page 1
  - Clicking Next then Prev returns to page 1
  - Scroll position resets to 0 after page navigation
- [ ] Existing `document-viewer.spec.ts` test "output tabs switch correctly" must continue to
      pass (it currently relies on the fallback mode; after adding the pages mock the
      MarkdownTab will switch to paginated mode — the test content assertion must still hold)

### Nice-to-Have
- [ ] Test that MarkdownTab enters fallback mode when `/markdown/pages` returns 404
      (mock a specific job that returns 404 for the pages endpoint only)
- [ ] Test that the page indicator label reads "1 / N" before any navigation

## Technical Design

### Data Models
No new data models. Tests use mock data only.

**New fixtures to add to `fixtures.ts`:**

```
MOCK_MARKDOWN_PAGES = {
  job_id: 'job-001',
  total_pages: 3,
  pages: [1, 2, 3]
}

MOCK_MARKDOWN_PAGE_1 = {
  job_id: 'job-001',
  page_number: 1,
  total_pages: 3,
  content: '# Parsed Document\n\nSample body text for testing.\n'
}

MOCK_MARKDOWN_PAGE_2 = {
  job_id: 'job-001',
  page_number: 2,
  total_pages: 3,
  content: '## Section Two\n\nContent on page two.\n'
}

MOCK_MARKDOWN_PAGE_3 = {
  job_id: 'job-001',
  page_number: 3,
  total_pages: 3,
  content: '## Section Three\n\nContent on page three.\n'
}
```

### API Endpoints
No new backend endpoints. Endpoints introduced in Sprint 7 are being tested:

| Method | Path | Response Shape |
|--------|------|---------------|
| GET | /api/jobs/{id}/markdown/pages | `{ job_id, total_pages, pages: number[] }` |
| GET | /api/jobs/{id}/markdown/pages/{page_num} | `{ job_id, page_number, total_pages, content }` |

### Route Mock Pattern
The mock for the per-page endpoint must capture different page numbers and respond with
different content. The recommended approach is to match the wildcard route
`**/api/jobs/*/markdown/pages/*` and inspect `route.request().url()` to extract the page
number, then return the appropriate fixture object.

Alternatively, register three separate exact-path mocks:
- `**/api/jobs/job-001/markdown/pages/1` -> MOCK_MARKDOWN_PAGE_1
- `**/api/jobs/job-001/markdown/pages/2` -> MOCK_MARKDOWN_PAGE_2
- `**/api/jobs/job-001/markdown/pages/3` -> MOCK_MARKDOWN_PAGE_3

The wildcard approach is preferred for maintainability. The implementation in `helpers.ts`
should use the URL-based dispatch pattern already present in the `chunks` mock (lines 44-47).

**Important ordering note**: The wildcard `**/api/jobs/*/markdown/pages/*` must be
registered BEFORE `**/api/jobs/*/markdown/pages` (no trailing path segment) to avoid
Playwright's route matching shadowing the more-specific path. Register the single-page
mock first.

### Existing Mock Conflict
The existing `document-viewer.spec.ts` test "output tabs switch correctly" (line 22)
currently asserts `await expect(page.getByText('Parsed Document')).toBeVisible()` which
works because `helpers.ts` has no pages mock, causing a 404, which triggers MarkdownTab
fallback mode that renders the full `MOCK_MARKDOWN` content (containing "# Parsed Document").

After adding the pages mock, MarkdownTab will load in paginated mode and render
`MOCK_MARKDOWN_PAGE_1` content instead (which must also contain "Parsed Document"). The
fixture must be designed this way — do not change the assertion in `document-viewer.spec.ts`.
`MOCK_MARKDOWN_PAGE_1.content` must start with `# Parsed Document`.

### UI Layout
No new UI. The tests target the existing MarkdownTab layout:

```
+----------------------------------------------+
| Markdown                 <  1 / 3  >          |  <- nav bar
+----------------------------------------------+
|                                              |
|  # Parsed Document                           |  <- content area (scrollable)
|  Sample body text for testing.               |
|                                              |
+----------------------------------------------+
```

Selectors to use in tests:
- Prev button: `page.locator('button:has-text("\u2039")')` (the rendered lsaquo character)
- Next button: `page.locator('button:has-text("\u203a")')` (the rendered rsaquo character)
- Page indicator: `page.getByText(/\d+ \/ \d+/)` — matches "1 / 3" pattern
- Content area: identified by unique text in `MOCK_MARKDOWN_PAGE_*` content
- The MarkdownTab is the default active tab; no tab-click needed to activate it

**Note on scroll reset test**: Use `page.evaluate(() => document.querySelector('.markdown-body')?.scrollTop ?? 0)` or a more robust selector targeting the scrollable container. Since the content div uses `ref={contentRef}` with no data-testid, the test can either scroll the content div programmatically first then navigate, then assert `scrollTop === 0`, or it can add a data-testid to the content area. If no data-testid exists, use the first `.overflow-y-auto` child of the markdown nav bar's parent.

## Sprint Plan

### Sprint 1: Markdown Viewer Test Coverage
Goal: Add `MOCK_MARKDOWN_PAGES` + `MOCK_MARKDOWN_PAGE_*` fixtures, update `helpers.ts` to
mock the two new endpoints, and add `markdown-viewer.spec.ts` with full pagination coverage.
All 18 existing Playwright tests must remain green.

Scope:
- [ ] Add `MOCK_MARKDOWN_PAGES`, `MOCK_MARKDOWN_PAGE_1`, `MOCK_MARKDOWN_PAGE_2`,
      `MOCK_MARKDOWN_PAGE_3` constants to `src/frontend/e2e/fixtures.ts` and export them
- [ ] Import new fixtures in `helpers.ts`
- [ ] Add route mock for `**/api/jobs/*/markdown/pages/*` (single page dispatch) in
      `mockAllApis` in `helpers.ts` — extract page number from URL and return matching fixture
- [ ] Add route mock for `**/api/jobs/*/markdown/pages` (pages list) in `mockAllApis`
      in `helpers.ts` — register AFTER the single-page mock
- [ ] Create `src/frontend/e2e/markdown-viewer.spec.ts`:
  - `describe('MarkdownTab Pagination')` block with `beforeEach` calling `mockAllApis`
  - Test: "Prev button is disabled on first page"
  - Test: "Next button is enabled on first page"
  - Test: "Next click advances page indicator to 2 / 3"
  - Test: "Page content changes after Next click"
  - Test: "Next button is disabled on last page"
  - Test: "Prev button is enabled after advancing past page 1"
  - Test: "Prev click after Next returns to page 1 content"
  - Test: "Scroll resets to top after page navigation"
- [ ] (Nice-to-have) Test: "Fallback mode renders full content when pages endpoint returns 404"
      — use `page.route()` override inside the test to return 404 for the pages list endpoint,
      then verify full `MOCK_MARKDOWN` text renders and no page indicator is visible

Success criteria (each independently verifiable):
- `npx playwright test --project=chromium markdown-viewer` exits with 0 and reports
  8+ passed, 0 failed
- `npx playwright test --project=chromium` exits with 0 and all 18+ tests pass (no
  regressions in `document-viewer.spec.ts`, `navigation.spec.ts`, `sidebar.spec.ts`,
  `upload-delete.spec.ts`)
- `npm run build` in `src/frontend` exits with 0 (TypeScript compiles cleanly)
- `npx eslint . --ext ts,tsx --max-warnings 0` in `src/frontend` exits with 0

Out of scope:
- Backend changes of any kind
- Adding `aria-label` or `data-testid` attributes to `MarkdownTab.tsx` (acceptable only if
  the scroll-reset test is otherwise unwritable; treat as last resort)
- Keyboard navigation tests (deferred to a future Sprint)
- Accessibility audits

## Design Direction
This Sprint adds no new UI. Design direction applies only to future MarkdownTab work.

- **Mood / Identity**: Developer utility — calm, functional, content-forward. The
  navigation chrome should recede so document content is the primary visual element.
- **Color direction**: Cool-neutral. `bg-white` nav bar with `border-b` separator.
  Buttons use `text-gray-600` at rest, `hover:bg-gray-100` on hover, `disabled:opacity-30`
  at boundary. No primary-color accent on navigation arrows.
- **Reference style**: VS Code editor tab panel — the UI surface becomes invisible and
  the document content fills the viewport.
- **Anti-patterns**: No floating page input fields, no progress bars, no skeleton loaders
  for page transitions, no color-coded page indicators, no pill-style page number buttons.
- **Key UX moments**: Page transition snap-in should feel immediate on fast connections.
  The only perceptible state change is the page indicator number and the content text.

## Risks & Dependencies

| Risk | Mitigation |
|------|-----------|
| Route matching order: `pages/*` shadowed by `pages` glob | Register single-page mock first in `mockAllApis`; test both endpoints independently in `markdown-viewer.spec.ts` |
| Unicode button text `\u2039`/`\u203a` may not match Playwright locator reliably | Use `locator('button').filter({ hasText: '\u2039' })` pattern; fall back to `nth(0)`/`nth(1)` button locators within the nav bar if needed |
| `document-viewer.spec.ts` "output tabs switch correctly" breaks if page-1 mock content lacks "Parsed Document" | Design constraint: `MOCK_MARKDOWN_PAGE_1.content` must begin with `# Parsed Document` |
| `fixtures.ts` may approach 300-line limit after additions | Keep fixture content strings to one short paragraph each; split into `fixtures-markdown.ts` and re-export from `fixtures.ts` if the file exceeds 280 lines post-edit |
| Scroll-reset assertion requires finding the scrollable div with no data-testid | Use `.overflow-y-auto` CSS class selector; if the selector is ambiguous, add `data-testid="markdown-content"` to the content div in `MarkdownTab.tsx` as a minimal targeted change |
