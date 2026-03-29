# Feature Spec: Delete (Trash) Finished Jobs

## Summary
Add soft-delete (trash) capability for completed/failed jobs. Users can trash a job
from the job list; trashed jobs disappear from the main list. The backend records a
`deleted_at` timestamp rather than immediately purging DB rows.

## Sprint Breakdown

### Sprint 1 — Backend DELETE endpoint + soft-delete model

**Goals:**
- Add `deleted_at: DateTime | None` column to `Job` model
- Add DB migration for existing SQLite databases (ALTER TABLE with try/except)
- Add `DELETE /api/jobs/{job_id}` endpoint:
  - Returns 404 if job not found or already deleted
  - Returns 400 if job is `pending` or `running`
  - Sets `deleted_at = utcnow()`, returns `{"job_id": ..., "status": "deleted"}`
- Update `GET /api/jobs` to exclude deleted jobs (filter `deleted_at IS NULL`)
- Update `GET /api/jobs/{job_id}` to return 404 for deleted jobs
- All existing tests must remain green; new tests added for delete behavior

**Success Criteria:**
1. `DELETE /api/jobs/{job_id}` returns 200 for a completed/failed job
2. After deletion, `GET /api/jobs/{job_id}` returns 404
3. `GET /api/jobs` does not include deleted jobs in results
4. `DELETE` on a pending/running job returns 400
5. All existing tests pass

### Sprint 2 — Frontend delete button

**Goals:**
- Add a trash icon button for `completed` and `failed` rows in `JobList`
- Clicking shows an inline confirmation ("Delete?" [Yes] [No])
- On confirm: calls `deleteJob()`, removes row optimistically, refreshes list
- `pending` and `running` jobs have no delete button

**Success Criteria:**
1. Delete button visible only on completed/failed rows
2. Confirmation step prevents accidental deletes
3. After confirm, row disappears immediately (optimistic update)
4. Error state shown if delete fails
