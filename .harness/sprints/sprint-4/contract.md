# Sprint 4 Contract: React 18 → 19

## Goal
Upgrade react, react-dom, @types/react, @types/react-dom to v19.

## Success Criteria
- SC-1: `package.json` lists `react: "^19.0.0"`, `react-dom: "^19.0.0"`, `@types/react: "^19.0.0"`, `@types/react-dom: "^19.0.0"`
- SC-2: `npm install` completes without errors
- SC-3: `npm run build` exits 0 with zero TypeScript errors
- SC-4: No forwardRef, no bare useRef(), no React.FC usage (all verified clean in audit)

## Out of Scope
- Any other upgrades

## Technical Decisions
- All third-party deps (react-split, react-markdown, react-syntax-highlighter) declare compatible peer deps
- No source code changes expected
