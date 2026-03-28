# Feature Spec: Advanced PDF Parser (Multi-lingual, Korean-Focused)

## Overview
A full-stack web application that uses docling as the core parsing engine to extract text, tables, images, and layout information from multi-lingual PDFs (Korean, English, Japanese, Chinese). Users upload PDFs via a React web UI, jobs are processed asynchronously on a FastAPI backend, and results can be downloaded in JSON, Markdown, or plain text formats.

## Feature Requirements

### Must-Have
- [ ] PDF file upload via REST API (multipart/form-data)
- [ ] Async job processing with status tracking (pending, running, completed, failed)
- [ ] Multi-lingual text extraction: Korean, English, Japanese, Chinese (via docling + EasyOCR/tesseract)
- [ ] Table extraction from PDFs
- [ ] Image extraction from PDFs (stored as files, referenced in output)
- [ ] Layout information extraction (bounding boxes, reading order, element types)
- [ ] Export results as JSON, Markdown, and plain text
- [ ] SQLite storage for job metadata and parsed results (via SQLAlchemy)
- [ ] REST API: upload, job status, results retrieval, download
- [ ] React 18 + Vite + TailwindCSS frontend
- [ ] Web UI: PDF upload, job list, job status polling, results viewer, download button
- [ ] Job history listing with pagination

### Nice-to-Have
- [ ] Per-page preview of extracted content
- [ ] Confidence scores for OCR-extracted text
- [ ] Drag-and-drop file upload in the UI
- [ ] Search within parsed results
- [ ] Batch upload (multiple PDFs)
- [ ] Result caching (skip re-parsing identical files by hash)
- [ ] Docker Compose for one-command local setup

---

## Technical Design

### Directory Structure
```
src/
├── frontend/
│   ├── components/
│   │   ├── UploadZone.tsx
│   │   ├── JobList.tsx
│   │   ├── JobStatusBadge.tsx
│   │   ├── ResultsViewer.tsx
│   │   └── DownloadButtons.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   └── JobDetailPage.tsx
│   ├── hooks/
│   │   ├── useUpload.ts
│   │   └── useJobStatus.ts
│   ├── services/
│   │   └── api.ts
│   └── main.tsx
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   │   ├── job.py
│   │   └── result.py
│   ├── routes/
│   │   ├── upload.py
│   │   ├── jobs.py
│   │   └── results.py
│   ├── services/
│   │   ├── parser.py
│   │   └── exporter.py
│   └── config.py
├── tests/
│   ├── unit/
│   │   ├── test_parser.py
│   │   └── test_exporter.py
│   ├── integration/
│   │   └── test_api.py
│   └── e2e/
│       └── test_upload_flow.spec.ts
└── .harness/
    ├── spec.md
    └── sprints/
```

### Data Models

#### `jobs` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (str) | PK, auto-generated |
| filename | VARCHAR(255) | Original uploaded filename |
| file_path | VARCHAR(512) | Server-side stored path |
| file_hash | VARCHAR(64) | SHA-256 of file (for dedup) |
| status | VARCHAR | pending / running / completed / failed |
| error_message | TEXT | Populated on failure |
| created_at | DATETIME | UTC |
| updated_at | DATETIME | UTC, auto-updated |
| page_count | INTEGER | Filled after parsing |
| languages_detected | TEXT | JSON array of detected language codes |

#### `parsed_results` table
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PK, autoincrement |
| job_id | VARCHAR | FK → jobs.id |
| result_json | TEXT | Full docling output serialized as JSON |
| markdown_path | VARCHAR(512) | Path to .md export file |
| text_path | VARCHAR(512) | Path to .txt export file |
| json_path | VARCHAR(512) | Path to .json export file |
| image_dir | VARCHAR(512) | Directory containing extracted images |
| created_at | DATETIME | UTC |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/upload | Upload PDF file, create job, return job_id |
| GET | /api/jobs | List all jobs (paginated: ?page=1&limit=20) |
| GET | /api/jobs/{job_id} | Get job status and metadata |
| GET | /api/jobs/{job_id}/result | Get parsed result (JSON structure) |
| GET | /api/jobs/{job_id}/download/json | Download result as JSON file |
| GET | /api/jobs/{job_id}/download/markdown | Download result as .md file |
| GET | /api/jobs/{job_id}/download/text | Download result as .txt file |
| DELETE | /api/jobs/{job_id} | Delete job and associated files |
| GET | /health | Health check |

### UI Layout

#### Page 1: Home / Upload (/)
```
┌─────────────────────────────────────────────────────┐
│  [Logo] Veluga PDF Parser                           │
├─────────────────────────────────────────────────────┤
│   ┌─────────────────────────────────────────────┐  │
│   │  Drop PDF here or click to upload           │  │
│   │  Supported: Korean, English, Japanese, Chinese│ │
│   └─────────────────────────────────────────────┘  │
│   [Upload Button]                                   │
│  ─────── Recent Jobs ───────────────────────────── │
│  ┌──────────────────────────────────────────────┐  │
│  │ filename.pdf | 2026-03-29 | ● Completed | [→]│  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

#### Page 2: Job Detail (/jobs/:id)
```
┌─────────────────────────────────────────────────────┐
│  ← Back   document.pdf   ● Completed                │
│  Pages: 12  |  Languages: Korean, English           │
├─────────────────────────────────────────────────────┤
│  Download: [JSON] [Markdown] [Plain Text]           │
├─────────────────────────────────────────────────────┤
│  ┌─── Page Navigator ───┐  ┌── Content View ──────┐ │
│  │ Page 1  ●            │  │ [Text block]         │ │
│  │ Page 2               │  │ [Table]              │ │
│  └──────────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## Sprint Plan

### Sprint 1: Backend Core — docling Integration + Async Job Processing
- **Goal**: A working FastAPI backend that accepts PDF uploads, queues async parsing jobs, and stores results in SQLite.
- **Scope**:
  - Project scaffold: `src/backend/` directory, `requirements.txt`, `config.py`, `.env.example`
  - SQLAlchemy models: `Job`, `ParsedResult`, `database.py` with SQLite
  - `POST /api/upload` endpoint: accepts PDF via python-multipart, saves to `uploads/` directory, creates Job record with status=pending, triggers background task
  - `GET /health` endpoint
  - `GET /api/jobs/{job_id}` endpoint: returns job status
  - `services/parser.py`: wraps docling `DocumentConverter`, handles Korean (EasyOCR pipeline), extracts text/tables/images, serializes to internal dict schema
  - FastAPI `BackgroundTasks` integration: job status transitions (pending → running → completed/failed), error capture to `error_message`
  - Uploaded file storage: `uploads/{job_id}/input.pdf`, images to `uploads/{job_id}/images/`
- **Dependencies**: None (greenfield)
- **Success Criteria**:
  - `POST /api/upload` with a PDF returns a `job_id` and status=pending
  - `GET /api/jobs/{job_id}` returns job status correctly
  - Background task runs parser and updates job to completed or failed
  - `parsed_results` row exists in SQLite after completion
  - `pytest tests/unit/` passes
  - `pytest tests/integration/test_api.py` passes: upload → poll status → check DB

### Sprint 2: Full API + Storage + Export Formats
- **Goal**: Complete the REST API surface, implement all three export formats (JSON, Markdown, plain text), and add job listing with pagination.
- **Scope**:
  - `GET /api/jobs` with pagination (`?page`, `?limit`)
  - `GET /api/jobs/{job_id}/result` returns full structured result JSON
  - `services/exporter.py`:
    - `to_json()`: serialize result to downloadable JSON file
    - `to_markdown()`: convert pages/elements to Markdown with GFM tables
    - `to_text()`: plain text extraction preserving reading order
  - Export generation triggered after parsing completes
  - `GET /api/jobs/{job_id}/download/json` — FileResponse
  - `GET /api/jobs/{job_id}/download/markdown` — FileResponse
  - `GET /api/jobs/{job_id}/download/text` — FileResponse
  - `DELETE /api/jobs/{job_id}` — removes DB rows and `uploads/{job_id}/` directory
  - Error handling: 404 on missing jobs, 400 on non-PDF uploads, 500 with structured error body
  - CORS middleware configured for frontend dev server (localhost:5173)
- **Dependencies**: Sprint 1 complete
- **Success Criteria**:
  - `GET /api/jobs` returns paginated list with correct total count
  - All three download endpoints return correct file content-type and non-empty bodies
  - Markdown output contains GFM table syntax for PDFs with tables
  - DELETE cleans up filesystem artifacts
  - All integration tests pass

### Sprint 3: Frontend Web UI
- **Goal**: React 18 + Vite + TailwindCSS frontend with upload, job list, job status polling, results viewer, and download buttons.
- **Scope**:
  - Vite scaffold: `src/frontend/`, `package.json`, TailwindCSS v3, React Router v6
  - `services/api.ts`: typed fetch wrappers for all backend endpoints
  - `HomePage` (`/`): UploadZone + JobList with auto-refresh
  - `JobDetailPage` (`/jobs/:id`): polling, status badge, metadata, DownloadButtons, ResultsViewer
  - `useUpload` hook: manages upload state (idle/uploading/error)
  - `useJobStatus` hook: encapsulates polling logic with cleanup on unmount
  - Production build: FastAPI serves frontend via StaticFiles mount
- **Dependencies**: Sprint 2 complete (all API endpoints), CORS configured
- **Success Criteria**:
  - User can upload a PDF and see it in the job list
  - Job detail page shows real-time status updates via polling
  - All three download buttons trigger browser downloads
  - ResultsViewer renders text and table elements from a completed job
  - `npm run build` succeeds with no TypeScript errors

---

## Risks & Dependencies

- **docling install size**: docling pulls in PyTorch, EasyOCR — install time can exceed 5 minutes. Pin version in `requirements.txt`.
- **EasyOCR Korean model download**: First run downloads ~100 MB language models. Pre-download in setup script.
- **Tesseract system dependency**: `tesseract-ocr` and Korean language data must be installed at the OS level.
- **Large PDF async timeout**: FastAPI BackgroundTasks runs in-process; large PDFs may take 2-5 minutes. Acceptable for MVP.
- **SQLite concurrency**: Enable WAL mode (`PRAGMA journal_mode=WAL`) on engine connect.
- **CORS in production**: Use StaticFiles mount for same-origin production deployment.

---

## Tech Stack Decisions

| Layer | Choice | Reason |
|-------|--------|--------|
| PDF parsing | docling | Native multi-lingual support, Korean via EasyOCR |
| OCR (Korean) | EasyOCR (via docling) | Best Korean character recognition |
| Backend | FastAPI (Python 3.11+) | Async-native, auto OpenAPI docs |
| Async jobs | FastAPI BackgroundTasks | Sufficient for MVP |
| ORM / DB | SQLAlchemy 2.x + SQLite | Simple setup, file-based |
| File upload | python-multipart | Required by FastAPI |
| Frontend | React 18 + Vite + TailwindCSS | Fast dev server, modern DX |
| Routing | React Router v6 | Standard SPA routing |
| Testing (BE) | pytest + httpx | FastAPI-native async testing |
| Testing (E2E) | Playwright | Matches harness standard |
