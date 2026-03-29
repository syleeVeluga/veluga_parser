"""
GET /api/jobs/{job_id}/result — full structured result JSON (v2)
GET /api/jobs/{job_id}/chunks — pre-computed RAG chunks
GET /api/jobs/{job_id}/toc — table of contents
GET /api/jobs/{job_id}/elements — flat element list with filters
GET /api/jobs/{job_id}/download/{format} — file downloads
GET /api/jobs/{job_id}/images/{filename} — serve extracted image files
GET /api/jobs/{job_id}/pdf — serve the original uploaded PDF
"""
import json
import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models.job import Job
from src.backend.models.result import ParsedResult

router = APIRouter()


def _get_job_or_404(job_id: str, db: Session) -> Job:
    job = db.query(Job).filter(Job.id == job_id, Job.deleted_at.is_(None)).first()
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


@router.get("/jobs/{job_id}/pdf")
def get_pdf(job_id: str, db: Session = Depends(get_db)):
    job = _get_job_or_404(job_id, db)
    if job.status != "completed":
        raise HTTPException(status_code=404, detail="PDF not available until job is completed")
    if not job.file_path:
        raise HTTPException(status_code=404, detail="PDF file path not recorded")
    pdf_path = Path(job.file_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=\"{job.filename}\""},
    )


@router.get("/jobs/{job_id}/images/{filename}")
def get_image(job_id: str, filename: str, db: Session = Depends(get_db)):
    # Security: reject any path traversal attempts
    if filename != Path(filename).name or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    _get_job_or_404(job_id, db)
    parsed = db.query(ParsedResult).filter(ParsedResult.job_id == job_id).first()
    if not parsed or not parsed.image_dir:
        raise HTTPException(status_code=404, detail="Image directory not found")
    image_dir = Path(parsed.image_dir)
    image_path = image_dir / filename
    # Security: confirm resolved path is inside the image directory
    try:
        image_path.resolve().relative_to(image_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    media_type, _ = mimetypes.guess_type(filename)
    return FileResponse(path=str(image_path), media_type=media_type or "image/png")


def _require_completed(job: "Job") -> None:
    if job.status in ("pending", "running"):
        raise HTTPException(status_code=202, detail="Job is still processing")
    if job.status == "failed":
        raise HTTPException(status_code=422, detail="Job failed")


@router.get("/jobs/{job_id}/chunks")
def get_chunks(
    job_id: str,
    strategy: Optional[str] = Query(default=None, description="hierarchical | semantic | hybrid"),
    db: Session = Depends(get_db),
):
    """Return pre-computed RAG chunks. Optionally filter by strategy."""
    job = _get_job_or_404(job_id, db)
    _require_completed(job)
    parsed = _get_result_or_404(job_id, db)
    try:
        chunks_data = json.loads(parsed.chunks_json or "{}")
    except (json.JSONDecodeError, TypeError) as e:
        raise HTTPException(status_code=500, detail=f"Chunks data is corrupt: {e}")

    if strategy:
        if strategy not in ("hierarchical", "semantic", "hybrid"):
            raise HTTPException(status_code=400, detail="strategy must be hierarchical, semantic, or hybrid")
        return {"job_id": job_id, "strategy": strategy, "chunks": chunks_data.get(strategy, [])}
    return {"job_id": job_id, "strategy": "all", "chunks": chunks_data}


@router.get("/jobs/{job_id}/toc")
def get_toc(job_id: str, db: Session = Depends(get_db)):
    """Return the table of contents extracted from section headers."""
    job = _get_job_or_404(job_id, db)
    _require_completed(job)
    parsed = _get_result_or_404(job_id, db)
    try:
        toc = json.loads(parsed.toc_json or "[]")
    except (json.JSONDecodeError, TypeError):
        toc = []
    return {"job_id": job_id, "toc": toc}


@router.get("/jobs/{job_id}/elements")
def get_elements(
    job_id: str,
    type: Optional[str] = Query(default=None, description="Comma-separated element types to include"),
    page: Optional[int] = Query(default=None, description="Filter by page number"),
    exclude_headers: bool = Query(default=False, description="Exclude page_header and page_footer"),
    db: Session = Depends(get_db),
):
    """Return the flat element list with optional filters."""
    job = _get_job_or_404(job_id, db)
    _require_completed(job)
    parsed = _get_result_or_404(job_id, db)
    try:
        result_data = json.loads(parsed.result_json or "{}")
    except (json.JSONDecodeError, TypeError) as e:
        raise HTTPException(status_code=500, detail=f"Result data is corrupt: {e}")

    elements: list = result_data.get("elements", [])

    if type:
        allowed = {t.strip() for t in type.split(",")}
        elements = [e for e in elements if e.get("type") in allowed]
    if page is not None:
        elements = [e for e in elements if e.get("page_number") == page]
    if exclude_headers:
        elements = [e for e in elements if e.get("type") not in ("page_header", "page_footer")]

    return {"job_id": job_id, "total": len(elements), "elements": elements}


@router.get("/jobs/{job_id}/download/chunks")
def download_chunks(job_id: str, db: Session = Depends(get_db)):
    """Download the chunks.json export file."""
    job = _get_job_or_404(job_id, db)
    if job.status != "completed":
        raise HTTPException(status_code=404, detail="Result not ready")
    parsed = _get_result_or_404(job_id, db)
    chunks_path = getattr(parsed, "chunks_path", None)
    if chunks_path and Path(chunks_path).exists():
        return FileResponse(
            path=chunks_path,
            media_type="application/json",
            filename=f"{job_id}_chunks.json",
        )
    # Fallback: derive path from json_path
    if parsed.json_path:
        fallback = Path(parsed.json_path).parent / "chunks.json"
        if fallback.exists():
            return FileResponse(
                path=str(fallback),
                media_type="application/json",
                filename=f"{job_id}_chunks.json",
            )
    raise HTTPException(status_code=404, detail="Chunks export file not found")


