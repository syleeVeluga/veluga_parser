# Sprint 1 Contract: Backend DELETE endpoint (Trash feature)

## Goals
- Soft-delete via `deleted_at` column on `Job`
- `DELETE /api/jobs/{job_id}` endpoint
- Filter deleted jobs from list/get endpoints
- Existing tests remain green; new tests added

## Out of Scope
- Frontend changes (Sprint 2)
- Hard delete / file cleanup
- Trash restore endpoint
