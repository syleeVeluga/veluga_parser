# Feature Spec: Advanced RAG Chunking — Rich Metadata Extraction via Docling

## Overview

Enhance Veluga Parser to extract the full semantic structure of PDFs using Docling's native element model (no VLM, no external APIs). The output becomes a rich, element-typed document graph — title, subtitles, section hierarchy, body text, tables, figures, lists, equations, captions, footnotes, page headers/footers, page numbers, reading order, and a table of contents — stored in a new wire format purpose-built for Advanced RAG chunking. The architecture mirrors MinerU in spirit: a local, cost-zero pipeline that produces RAG-ready JSON with enough metadata to support any chunking strategy downstream.

---

## Current State (Baseline)

### Parser (`src/backend/services/parser.py`)
- Docling version: **2.82.0**
- Uses `DocumentConverter` with `PyPdfiumDocumentBackend`
- Iterates `doc.iterate_items()` and classifies only three types: `TextItem`, `TableItem`, `PictureItem`
- All `TextItem`s are collapsed to a single `type: "text"` — no distinction between titles, headers, body, captions, footnotes, list items, or equations
- No hierarchy level captured (`level` from `iterate_items()` is ignored)

### Output format (v1)
```json
{
  "pages": [{"page_number": 1, "elements": [...]}],
  "metadata": {"total_pages": 5, "languages": ["en", "ko"], "has_tables": true, "has_images": false}
}
```

### DB schema
- `jobs`: id, filename, file_path, file_hash, status, error_message, page_count, languages_detected, created_at, updated_at, deleted_at
- `parsed_results`: id, job_id, result_json, markdown_path, text_path, json_path, image_dir, created_at

---

## New Output Format (v2)

```json
{
  "schema_version": "2.0",
  "metadata": {
    "total_pages": 12,
    "languages": ["en", "ko"],
    "has_tables": true,
    "has_images": true,
    "has_equations": false,
    "has_code": false,
    "title": "Deep Learning for NLP",
    "authors": [],
    "page_dimensions": [{"page_number": 1, "width": 595.0, "height": 842.0}]
  },
  "toc": [{"level": 1, "text": "Introduction", "page_number": 2, "element_id": "elem_0007"}],
  "elements": [...],
  "pages": [...],
  "chunks": {
    "hierarchical": [...],
    "semantic": [...],
    "hybrid": [...]
  }
}
```

### Element object (v2)
```json
{
  "element_id": "elem_0042",
  "type": "section_header",
  "hierarchy_level": 2,
  "content": "3.2 Experimental Setup",
  "page_number": 5,
  "reading_order": 42,
  "bbox": [72.0, 310.5, 524.0, 328.0],
  "language": "en",
  "parent_id": "elem_0031",
  "parent_section": "3. Experiments",
  "label": "SECTION_HEADER"
}
```

### Element types
| `type` | Docling source |
|--------|---------------|
| `title` | DocItemLabel.TITLE |
| `section_header` | DocItemLabel.SECTION_HEADER |
| `text` | DocItemLabel.TEXT |
| `table` | TableItem |
| `image` | PictureItem |
| `figure` | DocItemLabel.FIGURE |
| `list` | DocItemLabel.LIST |
| `list_item` | DocItemLabel.LIST_ITEM |
| `caption` | DocItemLabel.CAPTION |
| `footnote` | DocItemLabel.FOOTNOTE |
| `formula` | DocItemLabel.FORMULA |
| `page_header` | DocItemLabel.PAGE_HEADER |
| `page_footer` | DocItemLabel.PAGE_FOOTER |
| `code` | DocItemLabel.CODE |
| `reference` | DocItemLabel.REFERENCE |

### Chunk objects
```json
{
  "chunk_id": "hc_003",
  "strategy": "hierarchical",
  "content": "3.2 Experimental Setup\n\nWe trained on ...",
  "token_estimate": 312,
  "element_ids": ["elem_0042", "elem_0043"],
  "page_numbers": [5, 6],
  "section_path": ["3. Experiments", "3.2 Experimental Setup"],
  "metadata": {"start_page": 5, "end_page": 6, "has_table": false, "has_image": false, "languages": ["en"]}
}
```

---

## Sprint Plan

### Sprint 1: Rich Element Extraction (Parser Rewrite)

**Goal:** Rewrite `parse_pdf()` to produce the v2 element schema using all Docling label types.

**Files changed:**
- `src/backend/services/parser.py` — complete rewrite
- `tests/unit/test_parser.py` — extended with new element type tests

**Key implementation:**
1. Replace `isinstance` branch with `DocItemLabel`-based dispatch table
2. Capture `reading_order` counter (sequential from `iterate_items`)
3. For `SectionHeaderItem`, read `.level` attribute → `hierarchy_level`
4. Assign `element_id` as `f"elem_{reading_order:04d}"`
5. Build running `section_stack` for `parent_id` / `parent_section` tracking
6. Collect `toc_entries` from all `section_header` and `title` elements
7. Caption linking: second pass to link captions to preceding table/image
8. `pages` array derived from `elements` (backward compat)
9. `chunks` is empty dict (filled Sprint 2)

**Success criteria:**
1. Returns `schema_version: "2.0"` on any PDF
2. Elements have `element_id`, `type`, `reading_order`, `page_number`, `bbox`
3. All 15 element type values produced from Docling labels
4. `hierarchy_level` set on `section_header` and `title`
5. `parent_section` set correctly for body elements
6. `toc` non-empty for PDFs with section headers
7. `metadata.title` populated from first `title` element
8. `pages` array present (backward compat)
9. `chunks` present as empty dict
10. All existing tests pass

---

### Sprint 2: Chunker Service + New API Endpoints

**Goal:** Implement three chunking strategies; wire into pipeline; add new endpoints; update DB schema.

**Files changed:**
- `src/backend/services/chunker.py` — new
- `src/backend/services/exporter.py` — add chunks export
- `src/backend/routes/results.py` — add /chunks, /toc, /elements, /download/chunks
- `src/backend/routes/upload.py` — call chunker, store enriched metadata
- `src/backend/models/job.py` — add doc_title, element_count, chunk_count, has_equations, has_code
- `src/backend/models/result.py` — add schema_version, chunks_json, toc_json, element_count
- `src/backend/database.py` — idempotent ALTER TABLE migrations
- `tests/unit/test_chunker.py` — new
- `tests/integration/test_api.py` — extend

**Chunking strategies:**
1. **Hierarchical** — one chunk per section, anchored by section_header
2. **Semantic** — tables/figures/formulas as atomic chunks; prose grouped separately
3. **Hybrid** — hierarchical first, then split oversized sections at paragraph boundaries (max 512 tokens)

**New API endpoints:**
- `GET /api/jobs/{job_id}/chunks?strategy=hierarchical|semantic|hybrid`
- `GET /api/jobs/{job_id}/toc`
- `GET /api/jobs/{job_id}/elements?type=...&page=...&exclude_headers=true`
- `GET /api/jobs/{job_id}/download/chunks`

**DB additions (idempotent ALTER TABLE):**
- jobs: `doc_title`, `element_count`, `chunk_count`, `has_equations`, `has_code`
- parsed_results: `schema_version`, `chunks_json`, `toc_json`, `element_count`

**Success criteria:**
1. `/result` returns v2 with `chunks` object (3 strategy keys)
2. `/chunks` returns 200 with chunk array
3. `/chunks?strategy=hierarchical` filters correctly
4. `/toc` returns TOC array
5. `/elements?type=section_header` filters correctly
6. `/elements?exclude_headers=true` excludes page_header/page_footer
7. `/download/chunks` returns downloadable JSON
8. Job list includes `doc_title`, `element_count`, `chunk_count`
9. Each chunk has all required fields
10. Hybrid chunks <= 512 tokens (unless single atomic element exceeds limit)
11. All tests pass

---

### Sprint 3: Frontend Rich Structure Viewer + Chunk Explorer

**Goal:** Update frontend to display v2 structure. Add Chunks tab, hierarchy-aware element rendering, TOC sidebar.

**Files changed:**
- `src/frontend/src/services/api.ts` — update types + new functions
- `src/frontend/src/components/ResultsViewer.tsx` — new element type renderers
- `src/frontend/src/components/tabs/StructuredTab.tsx` — rename to Structure, add TOC
- `src/frontend/src/components/tabs/ChunksTab.tsx` — new
- `src/frontend/src/components/TocSidebar.tsx` — new
- `src/frontend/src/components/OutputPane.tsx` — add Chunks tab
- `src/frontend/src/components/DownloadButtons.tsx` — add Chunks JSON button

**Success criteria:**
1. ChunksTab renders chunks for all 3 strategies
2. Strategy selector switches chunk list
3. section_path breadcrumb displayed on chunks
4. TocSidebar shows TOC; clicking navigates to page
5. SectionHeaderElement renders h1/h2/h3 visually
6. page_header/page_footer collapsed by default
7. Chunk search filters in real time
8. Chunks JSON download works
9. doc_title in JobList and JobDetailPage
10. No TypeScript errors (`tsc --noEmit`)

---

## Risks & Dependencies
- Docling label availability in 2.82.0 — verify imports before use
- `SectionHeaderItem.level` attribute — guard with hasattr/try-except
- `doc.pages` dict availability — guard with hasattr
- Large result_json size — mitigated by separate chunks_json column
- Caption linking heuristic — best-effort, not guaranteed for all PDFs

## Tech Stack Decisions
- No VLM, no external API calls
- Token estimation: `round(len(content.split()) * 1.3)` — no tokenizer dependency
- Chunking runs synchronously in _run_parse_job (fast, <1s for most docs)
- `pages` array preserved for full backward compat throughout all sprints
