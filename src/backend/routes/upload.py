"""
POST /api/upload — accepts a PDF file and queues an async parsing job.
"""
import hashlib
import json
import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.backend.config import MAX_UPLOAD_SIZE_BYTES, UPLOAD_DIR
from src.backend.database import get_db
from src.backend.models.job import Job
from src.backend.models.result import ParsedResult

logger = logging.getLogger(__name__)
router = APIRouter()


def _compute_sha256(path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _run_parse_job(job_id: str, file_path: Path, image_dir: Path) -> None:
    """Background task: run docling parser and save results to DB."""
    from src.backend.database import SessionLocal
    from src.backend.services.parser import parse_pdf

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in DB")
            return

        job.status = "running"
        db.commit()

        result = parse_pdf(file_path, image_dir)

        job.status = "completed"
        job.page_count = result["metadata"]["total_pages"]
        job.languages_detected = json.dumps(result["metadata"]["languages"])
        db.commit()

        parsed = ParsedResult(
            job_id=job_id,
            result_json=json.dumps(result),
            image_dir=str(image_dir),
        )
        db.add(parsed)
        db.commit()
        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        db.rollback()
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Validate MIME type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        # Also allow by extension
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    job_id = str(uuid.uuid4())
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    input_path = job_dir / "input.pdf"
    image_dir = job_dir / "images"

    # Stream file to disk with size check
    size = 0
    with open(input_path, "wb") as dest:
        while chunk := await file.read(65536):
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE_BYTES:
                dest.close()
                shutil.rmtree(job_dir, ignore_errors=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB",
                )
            dest.write(chunk)

    file_hash = _compute_sha256(input_path)

    job = Job(
        id=job_id,
        filename=file.filename or "upload.pdf",
        file_path=str(input_path),
        file_hash=file_hash,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_parse_job, job_id, input_path, image_dir)

    return {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "created_at": job.created_at.isoformat() + "Z",
    }
