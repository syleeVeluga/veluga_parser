# Sprint 2 Contract: Full API + Storage + Export Formats

## Sprint Goal
Complete the REST API surface, implement all three export formats (JSON, Markdown, plain text), add job listing with pagination, CORS, and DELETE endpoint.

## Implementation Goals
1. `GET /api/jobs` with pagination (`?page`, `?limit`)
2. `GET /api/jobs/{job_id}/result` returns full structured result JSON
3. `services/exporter.py` with `to_json()`, `to_markdown()`, `to_text()`
4. Export generation triggered after parsing; paths saved to `ParsedResult`
5. Download endpoints: `GET /api/jobs/{job_id}/download/{json|markdown|text}`
6. `DELETE /api/jobs/{job_id}` — removes DB rows + filesystem
7. Error handling: 404 on missing jobs, 400 on non-PDF, 500 structured error
8. CORS middleware (already done in Sprint 1, verify it's correct)

## Testable Success Criteria
- [ ] `GET /api/jobs` returns `{total, page, limit, items}` with correct counts
- [ ] `GET /api/jobs/{job_id}/result` returns the internal result schema JSON
- [ ] `GET /api/jobs/{job_id}/download/json` returns JSON file (Content-Disposition: attachment)
- [ ] `GET /api/jobs/{job_id}/download/markdown` returns .md file
- [ ] `GET /api/jobs/{job_id}/download/text` returns .txt file
- [ ] Markdown output uses GFM table syntax for PDFs containing tables
- [ ] `DELETE /api/jobs/{job_id}` removes DB rows AND `uploads/{job_id}/` directory
- [ ] All three download endpoints return 404 for non-existent jobs
- [ ] All three download endpoints return 404 if result not ready (pending/running)
- [ ] `pytest tests/integration/test_api.py` covers all new endpoints

## Out-of-Scope for This Sprint
- Frontend UI — Sprint 3
- Real docling parsing (tests use mocked parser)
- Celery/Redis job queuing

## Technical Decisions
- Export files generated in background task (after parse_pdf succeeds)
- Exporter called from `_run_parse_job` in upload.py after parse succeeds
- Markdown tables use GFM syntax: `| col | col |\n|---|---|\n| val | val |`
- Text export: join all element content with newlines, preserving page breaks
- File paths saved to `ParsedResult.json_path`, `markdown_path`, `text_path`
- `DELETE` uses `shutil.rmtree` for filesystem cleanup
- Results endpoint returns 404 if job not found, 202 if job still pending/running
