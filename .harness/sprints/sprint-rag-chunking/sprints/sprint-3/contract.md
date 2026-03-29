# Sprint 3 Contract: Tailwind CSS 3 → 4

## Goal
Migrate from Tailwind v3 (PostCSS-based) to Tailwind v4 (CSS-first, Vite plugin).

## Success Criteria
- SC-1: `package.json` lists `tailwindcss: "^4.0.0"` and `@tailwindcss/vite` added; `autoprefixer` removed
- SC-2: `npm install` completes without errors
- SC-3: `npm run build` exits 0 with zero TypeScript errors
- SC-4: `src/styles/index.css` uses `@import "tailwindcss"` (no `@tailwind` directives)
- SC-5: `vite.config.ts` has `tailwindcss()` in plugins array
- SC-6: All `flex-shrink-0` renamed to `shrink-0` in all TSX files

## Out of Scope
- Adding new Tailwind v4 features
- Any other upgrades

## Technical Decisions
- Use @tailwindcss/vite (v4 Vite plugin), not PostCSS
- Delete tailwind.config.js (v4 auto-detects content)
- Remove autoprefixer (no longer needed)
