# Final Report: Frontend Major Dependency Upgrades (Sprint 6)

**Date:** 2026-03-29
**Sprint:** 6
**Result:** PASS (5/5 sprints, 25/25 criteria)

## Implemented Upgrades

| Package | From | To | Sprint |
|---------|------|----|--------|
| react-router-dom | ^6.28.0 | ^7.0.0 | 1 |
| vite | ^6.0.3 | ^8.0.0 | 2 |
| @vitejs/plugin-react | ^4.3.4 | ^6.0.0 | 2 |
| tailwindcss | ^3.4.15 | ^4.0.0 | 3 |
| @tailwindcss/vite | (new) | ^4.0.0 | 3 |
| autoprefixer | ^10.4.20 | removed | 3 |
| react | ^18.3.1 | ^19.0.0 | 4 |
| react-dom | ^18.3.1 | ^19.0.0 | 4 |
| @types/react | ^18.3.12 | ^19.0.0 | 4 |
| @types/react-dom | ^18.3.1 | ^19.0.0 | 4 |
| typescript | ^5.6.3 | ^6.0.0 | 5 |

## Breaking Changes Resolved

### react-router-dom 7
- No breaking changes hit — all v6 APIs used (`createBrowserRouter`, `RouterProvider`, `Link`, `useParams`, `Navigate`, `Outlet`) are unchanged in v7.

### Vite 8
- `vite.config.ts`: proxy string shorthand → object form `{ target: 'http://...', changeOrigin: false }`
- `@vitejs/plugin-react` upgraded to v6 (Vite 8 peer dep)

### Tailwind CSS 4
- `tailwind.config.js` deleted (v4 auto-detects content)
- `postcss.config.js` emptied (v4 Vite plugin replaces PostCSS integration)
- `src/styles/index.css`: `@tailwind base/components/utilities` → `@import "tailwindcss"`
- `vite.config.ts`: added `tailwindcss()` plugin from `@tailwindcss/vite`
- All `flex-shrink-0` renamed to `shrink-0` (3 files: OutputPane.tsx, ResultsViewer.tsx, JobDetailPage.tsx)

### React 19
- No breaking changes hit — codebase was already clean: no `forwardRef`, no `React.FC`, no bare `useRef()`, no `Context.Provider`, no legacy `ReactDOM.render`. All `useRef` calls already had initial values.
- Third-party libs (react-split, react-markdown, react-syntax-highlighter) all declare compatible peer deps.

### TypeScript 6
- Added `src/vite-env.d.ts` with `/// <reference types="vite/client" />` to fix new TS2882 error on CSS side-effect imports
- `typescript-eslint@8.x` peer dep cap is `<6.0.0` but works at runtime with `--legacy-peer-deps`; lint exits 0

## Test Results
- `pytest`: 42/42 passed
- `npm run build`: exit 0, 953 modules transformed, 0 TypeScript errors
- `npm run lint`: exit 0, 0 warnings
- `tsc --noEmit`: exit 0

## Known Limitations
- `typescript-eslint@8.x` declares peer dep `typescript <6.0.0` — no stable TS6-compatible release exists yet. Works at runtime but will show peer dep warnings. Update when typescript-eslint@9+ is released.
- Bundle size advisory: JS chunk is 508 kB (Vite warns at 500 kB) — out of scope for this upgrade sprint.

## Commits
- `3ac08ab` — chore(frontend): upgrade react-router-dom to v7
- `ba219d3` — chore(frontend): upgrade vite to v8 and @vitejs/plugin-react to v6
- `aa61718` — chore(frontend): upgrade tailwindcss to v4 with CSS-first config
- `bf98b1d` — chore(frontend): upgrade react and react-dom to v19
- `58c3622` — chore(frontend): upgrade typescript to v6; add vite-env.d.ts for TS2882 fix
