"""
GET /api/jobs/{job_id}/result — full structured result JSON
GET /api/jobs/{job_id}/download/{format} — file downloads
DELETE /api/jobs/{job_id} — delete job and files
"""
import json
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models.job import Job
from src.backend.models.result import ParsedResult

router = APIRouter()


def _get_job_or_404(job_id: str, db: Session) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _get_result_or_404(job_id: str, db: Session) -> ParsedResult:
    result = db.query(ParsedResult).filter(ParsedResult.job_id == job_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.get("/jobs/{job_id}/result")
def get_result(job_id: str, db: Session = Depends(get_db)):
    job = _get_job_or_404(job_id, db)
    if job.status in ("pending", "running"):
        return JSONResponse(
            status_code=202,
            content={"detail": "Job is still processing", "status": job.status},
        )
    if job.status == "failed":
        raise HTTPException(
            status_code=422,
            detail={"message": "Job failed", "error": job.error_message},
        )
    parsed = _get_result_or_404(job_id, db)
    try:
        return json.loads(parsed.result_json)
    except (json.JSONDecodeError, TypeError) as e:
        raise HTTPException(status_code=500, detail=f"Result data is corrupt: {e}")


@router.get("/jobs/{job_id}/download/json")
def download_json(job_id: str, db: Session = Depends(get_db)):
    job = _get_job_or_404(job_id, db)
    if job.status != "completed":
        raise HTTPException(status_code=404, detail="Result not ready")
    parsed = _get_result_or_404(job_id, db)
    if not parsed.json_path or not Path(parsed.json_path).exists():
        raise HTTPException(status_code=404, detail="JSON export file not found")
    return FileResponse(
        path=parsed.json_path,
        media_type="application/json",
        filename=f"{job_id}_result.json",
    )


@router.get("/jobs/{job_id}/download/markdown")
def download_markdown(job_id: str, db: Session = Depends(get_db)):
    job = _get_job_or_404(job_id, db)
    if job.status != "completed":
        raise HTTPException(status_code=404, detail="Result not ready")
    parsed = _get_result_or_404(job_id, db)
    if not parsed.markdown_path or not Path(parsed.markdown_path).exists():
        raise HTTPException(status_code=404, detail="Markdown export file not found")
    return FileResponse(
        path=parsed.markdown_path,
        media_type="text/markdown",
        filename=f"{job_id}_result.md",
    )


@router.get("/jobs/{job_id}/download/text")
def download_text(job_id: str, db: Session = Depends(get_db)):
    job = _get_job_or_404(job_id, db)
    if job.status != "completed":
        raise HTTPException(status_code=404, detail="Result not ready")
    parsed = _get_result_or_404(job_id, db)
    if not parsed.text_path or not Path(parsed.text_path).exists():
        raise HTTPException(status_code=404, detail="Text export file not found")
    return FileResponse(
        path=parsed.text_path,
        media_type="text/plain",
        filename=f"{job_id}_result.txt",
    )


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    job = _get_job_or_404(job_id, db)

    # Delete filesystem artifacts
    if job.file_path:
        job_dir = Path(job.file_path).parent
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)

    # Delete DB rows (result first due to FK)
    parsed = db.query(ParsedResult).filter(ParsedResult.job_id == job_id).first()
    if parsed:
        db.delete(parsed)
    db.delete(job)
    db.commit()

    return {"detail": "Job deleted", "job_id": job_id}
