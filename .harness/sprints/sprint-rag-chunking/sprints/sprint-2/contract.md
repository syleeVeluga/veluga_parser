# Sprint 2 Contract: Vite 6 → 8

## Goal
Upgrade Vite from ^6.0.3 to ^8.0.0 and @vitejs/plugin-react to the v8-compatible version.

## Success Criteria
- SC-1: `package.json` lists `vite: "^8.0.0"` and `@vitejs/plugin-react: "^6.0.0"`
- SC-2: `npm install` completes without errors
- SC-3: `npm run build` exits 0 with zero TypeScript errors
- SC-4: `vite.config.ts` proxy uses object form `{ target: 'http://localhost:8000' }` (not plain string)

## Out of Scope
- Tailwind v4 integration (Sprint 3)
- Any other upgrades

## Technical Decisions
- @vitejs/plugin-react@6.0.1 declares peerDependency vite@^8.0.0 — install it
- Vite 8 requires proxy target as object form, not plain string
