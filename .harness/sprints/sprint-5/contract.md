# Sprint 5 Contract: TypeScript 5 → 6

## Goal
Upgrade TypeScript from ^5.6.3 to ^6.0.0 and resolve any TS6 breaking changes.

## Success Criteria
- SC-1: `package.json` lists `typescript: "^6.0.0"`
- SC-2: `npm install` completes (--legacy-peer-deps acceptable due to typescript-eslint ecosystem lag)
- SC-3: `tsc --noEmit` exits 0 (zero TypeScript errors)
- SC-4: `npm run build` exits 0 with zero TypeScript errors
- SC-5: `npm run lint` exits 0, OR lint failure is documented as a known ecosystem limitation (typescript-eslint@8.x peer dep cap at TS<6.0.0)

## Out of Scope
- Updating typescript-eslint (no TS6-compatible stable release exists yet)

## Technical Decisions
- Use --legacy-peer-deps for install due to typescript-eslint@8 peer dep cap
- TypeScript 6.0.2 is the latest GA release (dist-tags.latest)
- Document any lint failures as known ecosystem gap, not a code problem
