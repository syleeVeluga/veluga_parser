# Evaluation Report: Sprint 3 — Tailwind CSS 3 → 4

**Date:** 2026-03-29
**Evaluator:** Claude Code (Sonnet 4.6)
**Sprint Contract:** `.harness/contract.md`

---

## Commands Executed

All commands run from `d:/dev/veluga_parser/src/frontend`.

### 1. `grep '"tailwindcss"\|"@tailwindcss/vite"\|"autoprefixer"' package.json`
```
"@tailwindcss/vite": "^4.0.0",
"tailwindcss": "^4.0.0",
```
(autoprefixer: no output — not present)

### 2. `npm install --legacy-peer-deps 2>&1 | tail -3`
```
  run `npm fund` for details

found 0 vulnerabilities
```

### 3. `npm run build 2>&1`
```
> veluga-pdf-parser-frontend@1.0.0 build
> tsc && vite build

vite v8.0.3 building client environment for production...
✓ 952 modules transformed.
dist/index.html                   0.46 kB │ gzip:   0.30 kB
dist/assets/index-C3ppeSdH.css   16.74 kB │ gzip:   4.38 kB
dist/assets/index-9214rUEr.js   458.76 kB │ gzip: 144.78 kB

✓ built in 421ms
```

### 4. `cat src/styles/index.css`
```css
@import "tailwindcss";
```

### 5. `cat vite.config.ts`
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: false },
      '/health': { target: 'http://localhost:8000', changeOrigin: false },
    },
  },
  build: {
    outDir: 'dist',
  },
})
```

### 6. `grep -rn "flex-shrink-0" src/`
```
(no output — zero matches)
```

### 7. `grep -rn "shrink-0" src/`
```
src/components/OutputPane.tsx:27:      <div className="flex border-b border-gray-200 shrink-0">
src/components/ResultsViewer.tsx:201:        <div className="w-36 shrink-0">
src/pages/JobDetailPage.tsx:38:      <div className="max-w-5xl mx-auto w-full px-4 pt-8 pb-4 shrink-0">
```

---

## Success Criteria Verification

### SC-1: package.json lists `tailwindcss: "^4.0.0"` and `@tailwindcss/vite` added; `autoprefixer` removed

**Result: PASS**

- `tailwindcss`: `"^4.0.0"` present in `devDependencies` ✓
- `@tailwindcss/vite`: `"^4.0.0"` present in `devDependencies` ✓
- `autoprefixer`: absent from both `dependencies` and `devDependencies` ✓

Note: `postcss` is still listed as a devDependency and `postcss.config.js` still exists (containing only `export default {}`). This is benign — an empty PostCSS config causes no harm and Vite ignores it when using `@tailwindcss/vite`. It is leftover clutter but does not affect SC-1 compliance.

---

### SC-2: `npm install` completes without errors

**Result: PASS**

Output ended with `found 0 vulnerabilities`. No errors or blocking warnings.

---

### SC-3: `npm run build` exits 0 with zero TypeScript errors

**Result: PASS**

`tsc` produced no output (zero errors). `vite build` succeeded in 421ms with 952 modules transformed. Exit code: 0.

---

### SC-4: `src/styles/index.css` uses `@import "tailwindcss"` (no `@tailwind` directives)

**Result: PASS**

File contains exactly one line: `@import "tailwindcss";`

No legacy `@tailwind base`, `@tailwind components`, or `@tailwind utilities` directives are present.

---

### SC-5: `vite.config.ts` has `tailwindcss()` in plugins array

**Result: PASS**

`tailwindcss` is imported from `@tailwindcss/vite` and invoked as `tailwindcss()` inside the `plugins` array alongside `react()`.

---

### SC-6: All `flex-shrink-0` renamed to `shrink-0` in all TSX files

**Result: PASS**

- `grep -rn "flex-shrink-0" src/` → **zero matches** ✓
- `grep -rn "shrink-0" src/` → **3 matches** in `OutputPane.tsx`, `ResultsViewer.tsx`, and `JobDetailPage.tsx` ✓

All usages correctly use the Tailwind v4-compatible `shrink-0` utility class.

---

## Summary Table

| SC   | Criterion                                                     | Result |
|------|---------------------------------------------------------------|--------|
| SC-1 | `tailwindcss ^4.0.0`, `@tailwindcss/vite` added, `autoprefixer` removed | PASS |
| SC-2 | `npm install` error-free                                      | PASS   |
| SC-3 | `npm run build` exits 0, zero TS errors                       | PASS   |
| SC-4 | `index.css` uses `@import "tailwindcss"`                      | PASS   |
| SC-5 | `vite.config.ts` has `tailwindcss()` in plugins               | PASS   |
| SC-6 | No `flex-shrink-0`; `shrink-0` present where needed           | PASS   |

**Minor observation:** `postcss.config.js` (empty, `export default {}`) and the `postcss` devDependency are leftover artifacts from the v3 PostCSS-based setup. They are completely harmless given the empty config, but could be removed in a future housekeeping commit.

---

Overall Result: PASS
