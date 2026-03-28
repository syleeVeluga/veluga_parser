# Final Report: Veluga PDF Parser

## Summary
Advanced multi-lingual PDF parser with special Korean PDF support, built using docling. Full-stack web application with FastAPI backend and React 18 frontend.

## Implemented Features

### Backend (FastAPI + Python 3.11+)
- **PDF Upload API**: `POST /api/upload` — multipart file upload with SHA-256 hashing, size validation, async job creation
- **Async Job Processing**: FastAPI BackgroundTasks — pending → running → completed/failed lifecycle
- **docling Integration**: `services/parser.py` — DocumentConverter with EasyOCR pipeline for Korean, Japanese, Chinese, English
- **Multi-lingual Detection**: Unicode-range heuristic for Korean/Japanese/Chinese/English (no heavy dependency)
- **SQLite Storage**: SQLAlchemy 2.x + WAL mode — `jobs` and `parsed_results` tables
- **Export Formats**: JSON, Markdown (GFM tables), plain text — generated after each successful parse
- **REST API**: 9 endpoints — upload, list jobs, get job, get result, download (3 formats), delete, health
- **Error Handling**: 400/404/409/422/500 with structured error bodies
- **CORS**: Configured for localhost:5173 and localhost:3000 (dev)
- **Production Serving**: FastAPI StaticFiles mount for React build

### Frontend (React 18 + Vite + TailwindCSS)
- **UploadZone**: Click-to-upload with client-side PDF MIME/extension validation
- **JobList**: Paginated table with auto-refresh (5s polling while active jobs exist)
- **JobStatusBadge**: Color-coded status (gray/yellow/green/red)
- **JobDetailPage**: 2-second polling while pending/running, stops on terminal state
- **DownloadButtons**: JSON / Markdown / Plain Text — disabled until job completes
- **ResultsViewer**: Page navigator sidebar + text/table/image element rendering
- **Typed API Layer**: `services/api.ts` — fully typed fetch wrappers, no `any`
- **Custom Hooks**: `useUpload` (idle/uploading/error state machine), `useJobStatus` (polling with cleanup)

## Final Test Results
- **Backend**: 42/42 tests passing (7 unit parser, 16 unit exporter, 19 integration API)
- **Frontend**: `npm run build` clean (0 TypeScript errors), ESLint 0 warnings/errors
- **Test coverage**: All API endpoints, error paths, export formats, language detection

## Sprint Results
| Sprint | Focus | Score | Result |
|--------|-------|-------|--------|
| 1 | Backend core (docling + async jobs + SQLite) | 86.3% | PASS |
| 2 | Full REST API + export formats + downloads | ~84% | PASS |
| 3 | React frontend + UI + static serving | 86.15% | PASS |

## Known Limitations
1. **docling not pre-installed**: `pip install docling` requires PyTorch + EasyOCR (~1-3GB). First run downloads Korean OCR models (~100MB to `~/.EasyOCR/`).
2. **Tesseract OS dependency**: Korean tesseract data (`tesseract-ocr-kor`) must be installed at OS level for tesseract OCR path.
3. **In-process async**: Large PDFs (100+ pages) block the FastAPI process during parsing. For production, upgrade to Celery + Redis.
4. **No auth**: No authentication or authorization — suitable for single-user local deployment only.
5. **File storage grows**: Requires periodic manual cleanup or `DELETE /api/jobs/{id}` calls.

## Future Improvements
- Celery + Redis for true async job queue (decouple parsing from web server)
- Docker Compose for one-command setup (includes tesseract + Korean language data)
- Playwright E2E tests for the upload → complete → download flow
- File deduplication by SHA-256 hash (skip re-parsing identical PDFs)
- Batch upload (multiple PDFs in one request)
- Confidence scores for OCR-extracted text
- Search within parsed results
- Authentication (JWT or API key)

## How to Run

### Backend
```bash
cd d:/dev/veluga_parser
pip install -r src/backend/requirements.txt
pip install docling  # heavy: ~1-3GB
uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (dev)
```bash
cd src/frontend
npm install
npm run dev  # http://localhost:5173 (proxies /api to :8000)
```

### Frontend (production)
```bash
cd src/frontend && npm run build
# FastAPI serves dist/ at http://localhost:8000/
```

### Tests
```bash
python -m pytest tests/ -v  # 42 backend tests
cd src/frontend && npm run build && npx eslint . --ext ts,tsx  # frontend
```
