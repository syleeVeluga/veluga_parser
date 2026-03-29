# Sprint 8 Contract: Markdown Viewer E2E Tests + Helper Mocks

## Goals
Add missing Playwright test coverage for Sprint 7's Markdown pagination feature.

## Success Criteria
1. `npx playwright test --project=chromium markdown-viewer` exits 0, 8+ tests pass, 0 fail
2. `npx playwright test --project=chromium` exits 0, all existing tests pass (no regressions)
3. `npm run build` in `src/frontend` exits 0
4. ESLint 0 warnings, 0 errors

## Deliverables
1. New fixtures in `src/frontend/e2e/fixtures.ts`: `MOCK_MARKDOWN_PAGES`, `MOCK_MARKDOWN_PAGE_1/2/3`
2. Updated `src/frontend/e2e/helpers.ts`: mocks for `/markdown/pages/*` and `/markdown/pages`
3. New `src/frontend/e2e/markdown-viewer.spec.ts` with 10 tests

## Out of Scope
- Backend changes
- Keyboard navigation
- Accessibility audits
