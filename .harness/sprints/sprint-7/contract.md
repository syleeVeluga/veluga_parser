# Sprint 1 Contract: Backend — Per-Page Markdown Generation and API

## Goals
Generate per-page Markdown using Docling's native export during PDF parsing, store on disk, and serve via two new API endpoints.

## Success Criteria
1. Uploading a multi-page PDF produces a `markdown_pages/` directory with one `.md` file per page
2. `GET /api/jobs/{job_id}/markdown/pages` returns 200 with `total_pages` and `pages` array
3. `GET /api/jobs/{job_id}/markdown/pages/1` returns 200 with non-empty `content`
4. `GET /api/jobs/{job_id}/markdown/pages/999` returns 404
5. `GET /api/jobs/{job_id}/download/markdown` still works (backward compat)
6. Reprocessing regenerates per-page Markdown files

## Implementation Tasks
- [ ] Add `markdown_pages_dir` column to ParsedResult model
- [ ] Modify `parse_pdf()` to generate per-page Markdown via Docling
- [ ] Add `to_page_markdowns()` to exporter.py
- [ ] Update `to_markdown()` to use native per-page Markdown
- [ ] Update `generate_all_exports()`
- [ ] Update `_run_parse_job()` in upload.py
- [ ] Add two new API endpoints in results.py
- [ ] Add DB migration for new column

## Out of Scope
- Frontend changes
- UI padding fixes
