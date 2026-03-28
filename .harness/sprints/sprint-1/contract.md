# Sprint 1 Contract: react-router-dom 6 → 7

## Goal
Upgrade react-router-dom from ^6.28.0 to ^7.0.0 with zero functional change to routing behaviour.

## Success Criteria
- SC-1: `package.json` lists `react-router-dom: "^7.0.0"`
- SC-2: `npm install` completes without errors
- SC-3: `npm run build` exits 0 with zero TypeScript errors
- SC-4: All routing imports (`Link`, `useParams`, `Navigate`, `Outlet`, `createBrowserRouter`, `RouterProvider`) still work without changes

## Out of Scope
- Any UI changes
- Any other dependency upgrades

## Technical Decisions
- react-router-dom v7 keeps the same `createBrowserRouter` / `RouterProvider` API
- No code changes expected; verify only
