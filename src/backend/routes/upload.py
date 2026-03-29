"""
POST /api/upload — accepts a PDF file and queues an async parsing job.
POST /api/jobs/{job_id}/reprocess — re-run parsing on an existing job.
"""
import hashlib
import json
import logging
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
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


_VALID_ENGINES = {"docling", "paddleocr", "gemini"}


def _run_parse_job(job_id: str, file_path: Path, image_dir: Path) -> None:
    """Background task: dispatch to the correct parser and save results to DB."""
    from src.backend.database import SessionLocal

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in DB")
            return

        job.status = "running"
        db.commit()

        engine = getattr(job, "engine", "docling") or "docling"
        t0 = time.monotonic()

        if engine == "paddleocr":
            from src.backend.services.parser_paddleocr import parse_pdf_paddleocr as _parse
            result = _parse(file_path, image_dir)
        elif engine == "gemini":
            from src.backend.services.parser_gemini import parse_pdf_gemini as _parse
            result = _parse(file_path, image_dir)
        else:
            from src.backend.services.parser import parse_pdf as _parse
            result = _parse(file_path, image_dir)

        parse_duration = time.monotonic() - t0

        from src.backend.services.structure_analyzer import analyze_structure
        result = analyze_structure(file_path, result)

        from src.backend.services.chunker import chunk_document
        result = chunk_document(result)

        from src.backend.services.exporter import generate_all_exports
        job_dir = file_path.parent
        export_paths = generate_all_exports(result, job_dir)

        meta = result.get("metadata", {})
        chunks = result.get("chunks", {})

        # Strip page_markdowns from result before DB storage (too large for SQLite)
        result.pop("page_markdowns", None)

        # Serialize and save ParsedResult first, then mark job completed.
        # This order prevents the job from appearing "completed" with no result row
        # if a serialization or DB error occurs between the two commits.
        structure_profile = meta.get("structure_profile", {})
        parsed = ParsedResult(
            job_id=job_id,
            schema_version=result.get("schema_version", "2.0"),
            result_json=json.dumps(result),
            chunks_json=json.dumps(chunks),
            toc_json=json.dumps(result.get("toc", [])),
            structure_json=json.dumps(structure_profile) if structure_profile else None,
            element_count=len(result.get("elements", [])),
            image_dir=str(image_dir),
            json_path=export_paths["json_path"],
            markdown_path=export_paths["markdown_path"],
            text_path=export_paths["text_path"],
            chunks_path=export_paths.get("chunks_path"),
            markdown_pages_dir=export_paths.get("markdown_pages_dir"),
        )
        db.add(parsed)
        db.commit()

        job.status = "completed"
        job.page_count = meta.get("total_pages", 0)
        job.languages_detected = json.dumps(meta.get("languages", []))
        job.doc_title = meta.get("title")
        job.element_count = len(result.get("elements", []))
        job.chunk_count = sum(len(v) for v in chunks.values())
        job.has_equations = bool(meta.get("has_equations", False))
        job.has_code = bool(meta.get("has_code", False))
        job.has_structure = bool(meta.get("has_structure_analysis", False))
        job.parse_duration_seconds = round(parse_duration, 2)
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
    engine: Optional[str] = Form(default="docling"),
    db: Session = Depends(get_db),
):
    # Validate engine
    if engine not in _VALID_ENGINES:
        engine = "docling"

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
        engine=engine or "docling",
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


class ReprocessRequest(BaseModel):
    engine: Optional[str] = None


@router.post("/jobs/{job_id}/reprocess")
async def reprocess_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    body: Optional[ReprocessRequest] = None,
    db: Session = Depends(get_db),
):
    """Re-run parsing + chunking on an existing job without re-uploading."""
    job = db.query(Job).filter(Job.id == job_id, Job.deleted_at.is_(None)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in ("pending", "running"):
        raise HTTPException(status_code=409, detail="Job is already processing")

    file_path = Path(job.file_path) if job.file_path else None
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=410, detail="Original PDF no longer on disk")

    # Apply engine override if provided
    if body and body.engine and body.engine in _VALID_ENGINES:
        job.engine = body.engine

    # Delete old result
    old_result = db.query(ParsedResult).filter(ParsedResult.job_id == job_id).first()
    if old_result:
        db.delete(old_result)

    # Reset job state
    job.status = "pending"
    job.error_message = None
    job.element_count = None
    job.chunk_count = None
    job.has_equations = None
    job.has_code = None
    db.commit()

    image_dir = file_path.parent / "images"
    background_tasks.add_task(_run_parse_job, job_id, file_path, image_dir)

    return {"job_id": job_id, "status": "pending"}
