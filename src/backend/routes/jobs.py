"""
GET /api/jobs — list jobs with pagination
GET /api/jobs/{job_id} — get single job status
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.backend.database import get_db
from src.backend.models.job import Job

router = APIRouter()


def _job_to_dict(job: Job) -> dict:
    langs = []
    if job.languages_detected:
        try:
            langs = json.loads(job.languages_detected)
        except Exception:
            langs = []
    return {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "page_count": job.page_count,
        "languages_detected": langs,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() + "Z" if job.created_at else None,
        "updated_at": job.updated_at.isoformat() + "Z" if job.updated_at else None,
    }


@router.get("/jobs")
def list_jobs(page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20
    offset = (page - 1) * limit
    total = db.query(func.count(Job.id)).scalar()
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [_job_to_dict(j) for j in jobs],
    }


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_dict(job)
