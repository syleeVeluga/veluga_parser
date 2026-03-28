# Feature Spec: Frontend Major Dependency Upgrades

## Overview
Migrate the React frontend (`src/frontend/`) from React 18 + Vite 6 + Tailwind CSS 3 + TypeScript 5 + react-router-dom 6 to React 19 + Vite 8 + Tailwind CSS 4 + TypeScript 6 + react-router-dom 7. All existing functionality must remain intact after each sprint.

## Feature Requirements

### Must-Have
- [ ] React 18 → 19: update `react`, `react-dom`, `@types/react`, `@types/react-dom`; resolve all React 19 breaking changes
- [ ] react-router-dom 6 → 7: update package; resolve all v7 breaking changes
- [ ] Vite 6 → 8: update `vite`, `@vitejs/plugin-react`; resolve all v8 config breaking changes
- [ ] Tailwind CSS 3 → 4: replace `tailwindcss` + PostCSS config + `tailwind.config.js` with v4 CSS-first configuration
- [ ] TypeScript 5 → 6: update `typescript`; resolve all TS 6 strict/breaking changes
- [ ] `npm run build` produces no errors after every sprint
- [ ] `npm run dev` hot-reloads correctly after every sprint
- [ ] All existing pages and components render without runtime errors after every sprint

### Nice-to-Have
- [ ] ESLint config updated for React 19 hooks lint rules
- [ ] `@vitejs/plugin-react` replaced with `@vitejs/plugin-react-swc` if react-swc becomes the recommended default for Vite 8

## Technical Design

### Data Models
No new data models. This is a pure dependency upgrade; backend is untouched.

### API Endpoints
No changes. All `/api/*` and `/health` proxied endpoints remain unchanged.

### UI Layout
No layout changes. All existing pages/components must render identically after migration:
- `Layout` (header + outlet)
- `HomePage` (UploadZone + JobList)
- `JobDetailPage` (metadata card, download buttons, split-pane viewer)
- All tab components (MarkdownTab, JsonTab, PlainTextTab, StructuredTab)

## Current Codebase Inventory

| File | Notes |
|---|---|
| `src/frontend/package.json` | React 18.3.1, Vite 6.0.3, Tailwind 3.4.15, TS 5.6.3, react-router-dom 6.28.0 |
| `src/frontend/vite.config.ts` | Minimal: react plugin + dev proxy |
| `src/frontend/tailwind.config.js` | Minimal: content glob, empty theme extend, no plugins |
| `src/frontend/postcss.config.js` | `tailwindcss: {}` + `autoprefixer: {}` |
| `src/frontend/src/styles/index.css` | Three directives: `@tailwind base/components/utilities` |
| `src/frontend/tsconfig.json` | `target: ES2020`, `moduleResolution: bundler`, strict mode, `noUnusedLocals/Parameters` |
| `src/frontend/eslint.config.js` | Flat config via `typescript-eslint`, react-hooks + react-refresh plugins |
| `src/frontend/src/main.tsx` | `createRoot` + `RouterProvider` + `createBrowserRouter` |
| All pages/components | Use `Link`, `useParams`, `Navigate`, `Outlet` from react-router-dom |

## Sprint Plan

---

### Sprint 1: Upgrade react-router-dom 6 → 7

**Goal:** Update routing package with zero functional change; this is isolated from all other upgrades and has the fewest breaking changes.

**Scope:**
- Update `react-router-dom` from `^6.28.0` to `^7.0.0` in `package.json`
- Run `npm install` to update `package-lock.json`
- Audit and fix all v7 breaking changes across the codebase:
  - `<Navigate>` component: verify `replace` prop behaviour (unchanged in v7 — confirm)
  - `useParams` generic signature: verify `useParams<{ jobId: string }>()` is still valid
  - `createBrowserRouter` / `RouterProvider`: verify API is unchanged (v7 keeps the same API; confirm no flags required)
  - v7 removes the legacy `<BrowserRouter>` default export for new apps — this app already uses `createBrowserRouter` so no change expected; verify anyway
  - Check for any deprecation warnings that became hard errors in v7 (e.g. `loader`, `action` not used here; confirm clean)
- Run `npm run build` — must exit 0

**Files likely touched:**
- `package.json`
- Potentially `src/main.tsx` if any v7 RouterProvider API changed

**Success Criteria:**
- `npm install` completes without peer dependency errors
- `npm run build` exits 0 with no TypeScript errors
- `npm run dev` starts; navigating to `/` and `/jobs/:jobId` routes works in browser
- No console errors on page load

---

### Sprint 2: Upgrade Vite 6 → 8

**Goal:** Update the build tool and its React plugin; keep the existing config working.

**Scope:**
- Update `vite` from `^6.0.3` to `^8.0.0` in `package.json`
- Update `@vitejs/plugin-react` from `^4.3.4` to the latest v8-compatible version
- Run `npm install`
- Audit and fix Vite 8 breaking changes:
  - **`server.proxy` config**: Vite 7 deprecated the plain-string shorthand for proxy targets; Vite 8 may require `{ target: 'http://localhost:8000' }` object form — update `vite.config.ts` accordingly
  - **`build.target` default**: Vite 8 may raise the default target; verify `tsconfig.json` `target: ES2020` is still compatible or adjust
  - **Node.js minimum version**: Verify Node.js version meets Vite 8's minimum requirement
  - **ESM-only internals**: Vite 8 is fully ESM; `"type": "module"` already set in `package.json` — confirm no CommonJS config files remain (postcss.config.js, tailwind.config.js use `export default` — confirm compatible)
  - **Plugin API changes**: Confirm `@vitejs/plugin-react` works with Vite 8 (use the version that lists `vite@8` in `peerDependencies`)
- Run `npm run build` — must exit 0

**Files likely touched:**
- `package.json`
- `vite.config.ts` (proxy shorthand → object form)

**Success Criteria:**
- `npm install` completes without peer dependency errors
- `npm run build` exits 0
- `npm run dev` starts and proxy to `http://localhost:8000` functions
- `npm run preview` works on the built output

---

### Sprint 3: Upgrade Tailwind CSS 3 → 4

**Goal:** Replace the Tailwind v3 PostCSS-based setup with the Tailwind v4 CSS-first approach. This is the most invasive sprint due to the complete configuration model change.

**Scope:**

**Package changes (`package.json`):**
- Remove `tailwindcss` v3, `autoprefixer` (no longer needed in v4 standalone)
- Install `tailwindcss` v4 (`^4.0.0`) and `@tailwindcss/vite` (v4's first-party Vite plugin)
- Remove or retain `postcss` only if still needed by other tools; remove `postcss-based tailwind` integration

**Config file changes:**
- Delete `tailwind.config.js` (v4 does not use JS config by default)
- Update `postcss.config.js`: remove `tailwindcss: {}` plugin entry; if `autoprefixer` is removed, delete the file or leave it empty
- Update `vite.config.ts`: add `import tailwindcss from '@tailwindcss/vite'` and add `tailwindcss()` to the `plugins` array (v4's recommended Vite integration)

**CSS changes (`src/styles/index.css`):**
- Replace the three `@tailwind` directives with the single v4 import:
  ```css
  @import "tailwindcss";
  ```
- v4 auto-detects content files so no `content` configuration is needed for the default setup

**Utility class audit** — scan all `.tsx` files for classes removed or renamed in v4:
- `flex-shrink-0` → renamed to `shrink-0` in v4 (breaking change — update all occurrences)
- `shadow-sm`, `rounded-xl`, `truncate`, `animate-spin`, `min-h-0`, `overflow-hidden` — verify still present in v4 core
- Color palette classes (`bg-gray-50`, `text-gray-500`, `border-gray-200`, `text-red-600`, `text-blue-600`) — v4 uses the same default palette names; confirm
- Responsive prefixes (`sm:grid-cols-4`) — prefix syntax unchanged; confirm

**Success Criteria:**
- `npm install` completes without peer dependency errors
- `npm run build` exits 0
- All Tailwind utility classes compile (no unknown utility class warnings in build output)
- `npm run dev` renders pages with correct visual styling (layout, colours, spacing visually identical)
- No `@tailwind` directive errors in the CSS build step

---

### Sprint 4: Upgrade React 18 → 19

**Goal:** Update React and its type definitions; resolve all React 19 breaking changes.

**Scope:**

**Package changes (`package.json`):**
- Update `react` and `react-dom` from `^18.3.1` to `^19.0.0`
- Update `@types/react` from `^18.3.12` to `^19.0.0`
- Update `@types/react-dom` from `^18.3.1` to `^19.0.0`
- Run `npm install`

**React 19 breaking changes to address:**

1. **`createRoot` API**: The call signature in `src/main.tsx` is `createRoot(rootElement).render(...)` — unchanged in React 19; confirm no update needed.

2. **`StrictMode` double-invocation**: React 19 changes how Strict Mode invokes effects (restored state is re-used instead of re-running). Existing hooks (`useJobStatus`, `useUpload`) may see changed behaviour with `useEffect` cleanup — audit and fix if polling timers fire incorrectly.

3. **Removed APIs (React 19 removes these entirely):**
   - `React.FC` type shorthand (still present in `@types/react@19` but `children` is removed from implicit props) — scan all components: none appear to use `React.FC`, but verify
   - `defaultProps` on function components — not used; confirm
   - `propTypes` — not used; confirm
   - `ReactDOM.render` (legacy root) — app already uses `createRoot`; no change

4. **`ref` as a prop (React 19 new behaviour):** React 19 forwards `ref` as a plain prop. If any component uses `React.forwardRef`, it must be updated to accept `ref` as a regular prop parameter instead. Scan all components for `forwardRef` usage — likely none, but verify.

5. **`useRef` requires an argument in React 19 `@types/react`:** All `useRef()` calls without an argument must become `useRef(null)` (or appropriate initial value). Scan all hooks and components for bare `useRef()`.

6. **Context API**: `<Context.Provider>` is replaced by `<Context>` as the provider in React 19. If any context providers exist, update. Scan codebase — likely none, but verify.

7. **`@types/react` v19 removes implicit `children` prop:** Any component typed with `React.FC` or `React.PropsWithChildren` without explicit `children` in the props interface will error. Fix by explicitly typing `children: React.ReactNode` where needed.

8. **Third-party peer deps**: `react-split@2`, `react-syntax-highlighter@16`, `react-markdown@10` must declare React 19 peer dep compatibility. If they do not, add `--legacy-peer-deps` to the install command and document the decision.

**Files likely touched:**
- `package.json`
- `src/hooks/useJobStatus.ts` (if `useRef` or effect cleanup needs fixing)
- `src/hooks/useUpload.ts` (same)
- Any component using `forwardRef` (likely none, but must verify)

**Success Criteria:**
- `npm install` completes without blocking peer dependency errors
- `npm run build` exits 0 with zero TypeScript errors
- `npm run dev` starts; all pages render without React runtime errors or console warnings
- Upload flow works (file selected → job created → polling → completion)
- Job detail page renders metadata, download buttons, and split-pane viewer

---

### Sprint 5: Upgrade TypeScript 5 → 6

**Goal:** Update the TypeScript compiler and resolve all breaking changes introduced in TS 6.

**Scope:**

**Package changes (`package.json`):**
- Update `typescript` from `^5.6.3` to `^6.0.0`
- Update `@typescript-eslint/eslint-plugin` and `@typescript-eslint/parser` to versions compatible with TS 6
- Update `typescript-eslint` to the latest version supporting TS 6
- Run `npm install`

**TypeScript 6 breaking changes to address:**

1. **`--moduleResolution bundler` compatibility**: TS 6 may change resolution behaviour for `bundler` mode — verify the existing `tsconfig.json` setting remains valid or update to whatever TS 6 recommends for Vite-based apps.

2. **Stricter type narrowing**: TS 6 introduces stricter control flow analysis. Run `tsc --noEmit` and fix all newly surfaced errors. Common patterns to check:
   - Nullable parameter access: `job?.filename ?? 'Job Detail'` — likely fine
   - `useParams<{ jobId: string }>()` returns `string | undefined` — existing `if (!jobId)` guard is correct; confirm still valid
   - Conditional rendering patterns with `&&` and nullable objects

3. **`isolatedModules` changes**: TS 6 may change how `isolatedModules` interacts with type-only imports. Ensure all type-only imports use `import type` where required — audit all `*.ts` and `*.tsx` files.

4. **`erasableSyntaxOnly` flag (TS 6 new flag)**: TS 6 introduces `--erasableSyntaxOnly` mode which may be set by default in new strict settings. If `enum` or `namespace` constructs are present, they must be replaced with `const` objects or ES modules. Scan codebase — likely none used, but verify.

5. **Removed/changed compiler options**: Verify all options in `tsconfig.json` are still valid in TS 6:
   - `useDefineForClassFields` — confirm still accepted
   - `moduleDetection: "force"` — confirm still accepted
   - `allowImportingTsExtensions` — confirm still accepted or update

6. **ESLint + TS 6 compatibility**: Update `@typescript-eslint/*` packages to a version that explicitly lists TypeScript 6 support. Run `npm run lint` and fix all new lint errors.

**Files likely touched:**
- `package.json`
- `tsconfig.json` (potentially options adjustments)
- `eslint.config.js` (plugin version updates)
- Source files if `import type` is missing or new TS 6 errors surface

**Success Criteria:**
- `npm install` completes without peer dependency errors
- `tsc --noEmit` exits 0 (no TypeScript errors)
- `npm run lint` exits 0 (no lint errors, zero warnings)
- `npm run build` exits 0
- `npm run dev` starts without errors

---

## Sprint Order Rationale

| Sprint | Upgrade | Rationale |
|---|---|---|
| 1 | react-router-dom 6 → 7 | Most isolated; routing-only changes; no peer dep conflicts |
| 2 | Vite 6 → 8 | Build tool only; no runtime impact; unblocks Tailwind v4 Vite plugin |
| 3 | Tailwind CSS 3 → 4 | Requires Vite 8 plugin; config model completely changes; isolated to CSS |
| 4 | React 18 → 19 | Runtime library; do after tooling is stable |
| 5 | TypeScript 5 → 6 | Type-checker last; catches all type issues introduced by prior upgrades |

## Risks & Dependencies

- **Peer dependency conflicts**: npm may refuse to install due to mismatched peer deps between upgraded packages. Use `--legacy-peer-deps` only as a last resort and document why.
- **`@vitejs/plugin-react` Vite 8 support**: Must confirm the plugin has a release supporting Vite 8 as a peer dep before upgrading Vite.
- **`@tailwindcss/vite` maturity**: Tailwind v4's Vite plugin (`@tailwindcss/vite`) is the recommended integration; confirm it is GA (not beta) before using it. Fall back to PostCSS integration if not.
- **`flex-shrink-0` → `shrink-0` rename**: This is a confirmed Tailwind v4 breaking change. All occurrences in JSX must be updated or the layout will break silently.
- **TypeScript 6 release status**: As of the spec date, TypeScript 6 may be in RC or beta. If only a pre-release is available, pin to the latest RC and note this as a known limitation.
- **`eslint-plugin-react-hooks` React 19**: The react-hooks plugin must support React 19's new hook rules (e.g. the `use()` hook). Update to the latest version that declares React 19 support.
- **`react-syntax-highlighter` and `react-split` compatibility**: These dependencies (`react-syntax-highlighter@16`, `react-split@2`) must declare peer dep compatibility with React 19. If they do not, they may require `--legacy-peer-deps` or replacement.
- **`react-markdown` compatibility**: `react-markdown@10` should support React 19; verify peer deps before Sprint 4.

## Out-of-Scope

- Backend changes (FastAPI, Python dependencies, database)
- New features or UI changes of any kind
- Adding tests (unit, integration, or E2E) beyond verifying the build passes
- Migrating to a different framework (e.g. Next.js, Remix)
- Migrating from `@vitejs/plugin-react` to `@vitejs/plugin-react-swc` (unless it becomes required for Vite 8)
- Adding new Tailwind v4 features (OKLCH colours, CSS variables API, container queries) — only migrate existing usage

## Tech Stack Decisions

- Use `@tailwindcss/vite` (v4's Vite plugin) as the primary Tailwind v4 integration, not PostCSS, since the project already uses Vite
- Keep `postcss.config.js` in place (simplified or empty) in case other PostCSS plugins are added later
- Do not change `moduleResolution: bundler` unless TypeScript 6 breaks it — this is the correct setting for Vite projects
- Each sprint ends with a `git commit` using conventional commit format: `chore(frontend): upgrade <package> to vN`
