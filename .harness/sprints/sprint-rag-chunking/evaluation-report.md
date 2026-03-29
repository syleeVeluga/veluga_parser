# Evaluation Report — Advanced RAG Chunking (Sprints 1, 2, 3)

**Date:** 2026-03-29
**Evaluator:** Independent QA (Claude Code)
**Feature:** Advanced RAG Chunking — Rich Metadata Extraction via Docling

---

## Overall Result: PASS

---

## Scores

| Category        | Score (0–100) | Weight | Weighted Score |
|-----------------|--------------|--------|---------------|
| Functionality   | 88           | 30%    | 26.4          |
| Code Quality    | 80           | 25%    | 20.0          |
| Testing         | 92           | 20%    | 18.4          |
| Security        | 90           | 15%    | 13.5          |
| UI/UX           | 85           | 10%    | 8.5           |
| **Total**       |              |        | **86.8**      |

All categories >= 50%. Total >= 70%. No Critical bugs. **PASS.**

---

## Test Results (Verbatim)

### Backend — pytest
```
116 passed in 1.80s
```
All 116 tests pass across:
- `tests/unit/test_parser.py` — 31 tests
- `tests/unit/test_chunker.py` — 30 tests
- `tests/unit/test_exporter.py` — 15 tests
- `tests/integration/test_api.py` — 37 tests (v2 schema / chunks / TOC / elements)

### Frontend — TypeScript check
```
npx tsc --noEmit → exit 0 (no output, zero errors)
```

### Frontend — Build
```
npm run build → exit 0
tsc + vite build: 991 modules, 0 TS errors
(Non-blocking warning: chunk > 500 kB)
```

### Frontend — ESLint
```
npm run lint → EXIT 1
ChunksTab.tsx:92:6 — react-hooks/exhaustive-deps: missing dependency 'strategy'
1 problem (0 errors, 1 warning) — exceeds max-warnings 0
```
ESLint fails. This is a Medium bug.

---

## Contract Item Results

### Sprint 1: Rich Element Extraction

- [PASS] SC-1: `schema_version: "2.0"` returned on any PDF — confirmed in integration tests and parser.py.
- [PASS] SC-2: Elements have `element_id`, `type`, `reading_order`, `page_number`, `bbox` — verified in parser and unit tests.
- [PASS] SC-3: All 15 element types in `LABEL_TYPE_MAP` (title, section_header, text, table, image, figure, list, list_item, caption, footnote, formula, page_header, page_footer, code, reference).
- [PASS] SC-4: `hierarchy_level` set on `section_header` via `_get_hierarchy_level()`; `title` gets level=0.
- [PASS] SC-5: `parent_section` set via `section_stack`; verified by `test_parent_section_set_on_body_element_after_header`.
- [PASS] SC-6: `toc` populated from title and section_header elements; two TOC tests pass.
- [PASS] SC-7: `metadata.title` from first title element; verified by test.
- [PASS] SC-8: `pages` array present for backward compat; `test_backward_compat_pages_array_present` passes.
- [PASS] SC-9: Parser returns `chunks: {}` (empty dict); chunker fills it downstream.
- [PASS] SC-10: All 116 tests pass.

### Sprint 2: Chunker Service + New API Endpoints

- [PASS] SC-1: `/result` returns v2 with `chunks` having 3 strategy keys — `test_result_chunks_has_three_strategies` passes.
- [PASS] SC-2: `/chunks` returns 200 with chunk array — `test_chunks_endpoint_returns_200_for_completed_job` passes.
- [PASS] SC-3: `/chunks?strategy=hierarchical` filters correctly — `test_chunks_strategy_filter_hierarchical` passes.
- [PASS] SC-4: `/toc` returns TOC array with correct fields — `test_toc_endpoint_returns_200` and `test_toc_has_expected_entries` pass.
- [PASS] SC-5: `/elements?type=section_header` filters by type — `test_elements_type_filter` passes.
- [PASS] SC-6: `/elements?exclude_headers=true` excludes page_header/page_footer — `test_elements_exclude_headers` passes.
- [PASS] SC-7: `/download/chunks` returns JSON file — `test_download_chunks_returns_json_for_completed_job` passes.
- [PASS] SC-8: Job list includes `doc_title`, `element_count`, `chunk_count` — confirmed in `jobs.py::_job_to_dict` and integration test.
- [PASS] SC-9: Each chunk has all required fields (chunk_id, strategy, content, token_estimate, element_ids, page_numbers, section_path, metadata) — confirmed in chunker.py and unit tests.
- [PASS] SC-10: Hybrid chunks <= 512 tokens unless single atomic element exceeds limit — manually verified with adversarial inputs (300-word elements). Atomics (table/image/figure/formula) are never split.
- [PASS] SC-11: All 116 tests pass.

### Sprint 3: Frontend Rich Structure Viewer + Chunk Explorer

- [PASS] SC-1: ChunksTab renders chunks for all 3 strategies — fetches all via `getChunks(jobId)`, stores in `allChunks` state.
- [PASS] SC-2: Strategy selector switches chunk list — second `useEffect([strategy, allChunks])` updates displayed list on selection change.
- [PASS] SC-3: `section_path` breadcrumb on chunks — ChunksTab lines 39–48 render path segments with `›` separators.
- [PASS] SC-4: TocSidebar shows TOC; clicking calls `onNavigate(page_number)` propagated through StructuredTab to ResultsViewer.
- [PASS] SC-5: SectionHeaderElement maps `hierarchy_level` → `text-xl/text-lg/text-base/text-sm` font sizes.
- [PASS] SC-6: page_header/page_footer collapsed by default — `CollapsibleElement` starts `open=false`.
- [PASS] SC-7: Chunk search filters in real time using `search` state on every render.
- [PASS] SC-8: Chunks JSON download in ChunksTab (inline `<a download>`) and DownloadButtons.
- [PASS] SC-9: `doc_title` shown in JobList (`JobList.tsx:127`) and JobDetailPage (`JobDetailPage.tsx:49–51`).
- [FAIL] SC-10: `tsc --noEmit` exits 0 (TS types fine), but `npm run lint` exits 1 due to `react-hooks/exhaustive-deps` warning in ChunksTab.tsx:92.

---

## Bugs Found

### Critical
None.

### High
None.

### Medium

**Bug M-1: ChunksTab.tsx — missing `useEffect` dependency causes lint failure**
- File: `src/frontend/src/components/tabs/ChunksTab.tsx`, Line 87, 92
- Issue: `useEffect(() => { ... setChunks(all[strategy] ?? []) ... }, [jobId])` reads `strategy` but does not include it in the dependency array. ESLint `react-hooks/exhaustive-deps` flags this, causing `npm run lint` to exit 1 (--max-warnings 0 policy).
- Impact: `npm run lint` is a CI quality gate. The stale-closure risk is mitigated in practice by a separate `useEffect([strategy, allChunks])`, but the lint violation stands.
- Fix: Remove line 87 (`setChunks(all[strategy] ?? [])`) from the fetch effect — trust the second effect to set `chunks` whenever `allChunks` or `strategy` changes.

**Bug M-2: results.py — Duplicate DELETE handler (dead code, semantic inconsistency)**
- File: `src/backend/routes/results.py`, Lines 244–264
- Issue: `results.py` defines `DELETE /api/jobs/{job_id}` as a hard-delete (DB row removed + filesystem deleted). `jobs.py` also defines `DELETE /api/jobs/{job_id}` as a soft-delete (`deleted_at` timestamp). Because `jobs_router` is registered before `results_router`, FastAPI always routes to jobs.py. The results.py handler is dead code.
- Impact: No runtime breakage today. If router order changes, hard-delete silently replaces soft-delete. The inconsistency creates maintenance confusion.
- Fix: Remove the DELETE handler from `results.py`.

**Bug M-3: results.py — `_get_job_or_404` ignores soft-delete**
- File: `src/backend/routes/results.py`, Lines 28–32
- Issue: `db.query(Job).filter(Job.id == job_id).first()` does not filter `deleted_at.is_(None)`. The new v2 endpoints (`/chunks`, `/toc`, `/elements`, `/pdf`) inherit this helper. A soft-deleted job would still be accessible via these endpoints.
- Impact: Currently low-risk (the delete in jobs.py sets `deleted_at` and the job remains in DB), but logically incorrect — soft-deleted resources should be invisible.
- Fix: Change filter to `db.query(Job).filter(Job.id == job_id, Job.deleted_at.is_(None)).first()`.

### Low

**Bug L-1: parser.py exceeds 300-line limit**
- File: `src/backend/services/parser.py` — 343 lines (CLAUDE.md limit: 300)
- Impact: Minor convention violation. No functional impact.

**Bug L-2: ResultsViewer.tsx exceeds 300-line limit**
- File: `src/frontend/src/components/ResultsViewer.tsx` — 322 lines
- Impact: Minor convention violation. Element sub-components could be extracted.

**Bug L-3: `list` element type has no dedicated renderer**
- File: `src/frontend/src/components/ResultsViewer.tsx`
- Issue: `ElementRenderer` switch has no `'list'` case — falls to `default: <TextElement>`. The container `list` element renders as plain text. `list_item` is correctly rendered with bullet+indent.
- Impact: Visual fidelity only; functionally acceptable since Docling emits list_item children.

**Bug L-4: `_estimate_tokens("")` returns 1 instead of 0**
- File: `src/backend/services/chunker.py`, Line 21
- Issue: `max(1, round(0 * 1.3))` = 1. Empty content chunks (e.g., images) report 1 token.
- Impact: Negligible — no functional effect on chunking behavior.

---

## Detailed Code Review

### What Went Well

- **Parser rewrite is clean and defensive**: All `hasattr`/`try-except` guards in place for Docling attributes (`prov`, `bbox`, `level`, `pages`), satisfying spec's documented risks.
- **Chunker is pure and side-effect-free**: No I/O or state. Three strategies cleanly separated with shared helpers. Hybrid correctly delegates to hierarchical then splits at token boundaries.
- **Test coverage is excellent**: 116 tests with meaningful assertions. Docling mocked cleanly. Edge cases covered: cross-page caption linking, empty documents, page-header-only documents, oversized atomics.
- **API endpoints properly structured**: Input validation (invalid strategy → 400), correct HTTP status codes (404/202/422), error propagation.
- **Security**: Path traversal check on image filenames uses both string check and `resolve().relative_to()` double-defense. No hardcoded secrets. No raw SQL. No `any` TypeScript type.
- **Frontend types are complete**: All 15 element types, full `ResultElement`/`Chunk`/`TocEntry` interfaces. v2 API functions (`getChunks`, `getToc`, `getElements`) all typed.
- **TOC navigation fully wired**: StructuredTab loads TOC, passes `activePage`/`onPageChange` bidirectionally between TocSidebar and ResultsViewer.
- **DB migrations are idempotent**: `try/except` on each ALTER TABLE — safe to run on existing schemas.
- **`list` and `list_item` in chunker `_BODY_TYPES`**: Both included, so they participate in chunking correctly even though `list` has no special renderer.

### Needs Improvement

- `src/frontend/src/components/tabs/ChunksTab.tsx`, Line 92: Remove `strategy` read from inside the `[jobId]`-only effect to fix lint.
- `src/backend/routes/results.py`, Lines 244–264: Remove dead DELETE handler.
- `src/backend/routes/results.py`, Lines 28–32: Add `deleted_at.is_(None)` filter.

---

## Required Fixes for FAIL

Not applicable — overall result is **PASS**. The following are strongly recommended for the next sprint:

1. **[Medium — blocks lint gate]** Fix `ChunksTab.tsx` useEffect missing dependency. Remove line 87 from the fetch effect.
2. **[Medium]** Remove dead DELETE handler from `results.py`.
3. **[Medium]** Add soft-delete filter to `_get_job_or_404` in `results.py`.
