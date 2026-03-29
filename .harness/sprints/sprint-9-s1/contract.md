# Sprint 1 Contract: Engine Abstraction + PaddleOCR Backend

## Goal
Establish the engine dispatch architecture and implement PaddleOCR 3 adapter so jobs can be submitted with `engine=paddleocr` and run end-to-end.

## Implementation Goals
1. Add `engine` and `parse_duration_seconds` columns to `Job` model
2. `POST /api/upload` accepts optional `engine` form field (default `"docling"`)
3. `_run_parse_job` dispatches to correct parser based on `job.engine`
4. `src/backend/services/parser_paddleocr.py` — `parse_pdf_paddleocr()` returns v2 schema result
5. `GET /api/jobs` and `GET /api/jobs/{id}` include `engine` field in response
6. `POST /api/jobs/{id}/reprocess` accepts optional `engine` JSON body override
7. `src/tests/test_engine_dispatch.py` — pytest coverage for engine routing (mocked parsers)
8. Update `JobSummary` TypeScript type with `engine` field

## Success Criteria (each independently testable)
- `POST /api/upload` with no engine → `GET /api/jobs/{id}` returns `"engine": "docling"`
- `POST /api/upload` with `engine=paddleocr` → job `engine` is `"paddleocr"`
- `POST /api/upload` with `engine=gemini` → job `engine` is `"gemini"` (stored, will fail at runtime)
- `pytest src/tests/test_engine_dispatch.py` all pass (parsers mocked)
- `GET /api/jobs` response includes `engine` field on each job object
- PaddleOCR parser import-guarded: app starts normally even if `paddleocr` package absent

## Out of Scope
- Gemini parser implementation (Sprint 2)
- Settings routes and UI (Sprint 2)
- Frontend engine selector (Sprint 3)

## Technical Decisions
- `engine` stored on Job row (String 20, default "docling")
- `parse_duration_seconds` Float, nullable
- Import dispatch inside `_run_parse_job` with deferred imports
- `parser_paddleocr.py` uses `pypdfium2` for page rendering
- PaddleOCR import guarded with try/except RuntimeError fallback
