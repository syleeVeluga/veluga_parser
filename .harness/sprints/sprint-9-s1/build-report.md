# Sprint 9 (Feature Sprint 1) Build Report: Engine Dispatch + PaddleOCR

## Status: COMPLETE

## What was implemented

### Backend
1. **Job model** — Added `engine` (String 20, default "docling") and `parse_duration_seconds` (Float, nullable)
2. **Database migrations** — Idempotent ALTER TABLE for both new columns
3. **upload.py** — Accepts `engine` form field; dispatches docling/paddleocr/gemini; records parse_duration_seconds
4. **reprocess endpoint** — Accepts optional JSON body `{ "engine": "..." }` override
5. **jobs.py** — `engine` and `parse_duration_seconds` in all job response dicts
6. **config.py** — `GEMINI_API_KEY` from `.env` via python-dotenv
7. **parser_paddleocr.py** — Full PaddleOCR 3 adapter (import-guarded, pypdfium2, v2 schema)
8. **parser_gemini.py** — Stub with import/key guard (full impl Sprint 2)

### Frontend
- `api.ts` — `EngineType` type + `engine`/`parse_duration_seconds` on `JobSummary`

### Tests
- `tests/integration/test_engine_dispatch.py` — 6 tests all pass

## Test Results
- 6/6 new tests pass
- 122/122 total backend tests pass (no regressions)
