"""
CoA API endpoints:
  POST   /api/coa/upload         Accept file, validate, store, trigger async pipeline
  GET    /api/coa/status/{id}    Poll processing status + page progress
  GET    /api/coa/result/{id}    Full structured result with validation
  GET    /api/coa/export/{id}    CSV or JSON download
  GET    /api/coa/submissions    Recent submission list for sidebar
"""
from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
import io

from app.config import get_settings
from app.core.extraction.intake import detect_mime_type, is_supported
from app.core.extraction.pipeline import run_pipeline
from app.core.export.exporter import generate_export
from app.db import queries
from app.db.models import SubmissionStatus
from app.storage.files import upload_coa_file

router = APIRouter()
logger = structlog.get_logger(__name__)
settings = get_settings()


def _ok(data: Any) -> dict[str, Any]:
    return {"data": data, "error": None}


def _err(code: str, message: str) -> dict[str, Any]:
    return {"data": None, "error": {"code": code, "message": message}}


@router.post("/upload", status_code=201)
async def upload_coa(
    file: UploadFile,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Accept a CoA file (PDF/JPG/PNG), persist it, and kick off async extraction."""
    if not file.filename:
        raise HTTPException(status_code=422, detail=_err("NO_FILENAME", "Filename is required"))

    file_bytes = await file.read()

    # Validate file size
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=422,
            detail=_err(
                "FILE_TOO_LARGE",
                f"File exceeds maximum size of {settings.max_file_size_mb} MB",
            ),
        )

    # Detect and validate MIME type
    mime_type = detect_mime_type(file.filename, file_bytes)
    if not is_supported(mime_type):
        raise HTTPException(
            status_code=422,
            detail=_err(
                "UNSUPPORTED_FILE_TYPE",
                f"File type '{mime_type}' is not supported. Accepted: PDF, JPG, PNG, TIFF",
            ),
        )

    # Create DB record first to get submission_id
    submission = await queries.create_submission(
        original_filename=file.filename,
        file_path="",  # will update after upload
        file_size_bytes=len(file_bytes),
        mime_type=mime_type,
    )
    submission_id = submission["id"]

    # Upload to Supabase Storage
    try:
        file_path = await upload_coa_file(file_bytes, file.filename, submission_id)
    except Exception as exc:
        logger.error("Storage upload failed", submission_id=submission_id, exc_info=exc)
        await queries.update_submission_status(
            submission_id,
            status=SubmissionStatus.FAILED,
            error_message="File storage upload failed",
        )
        raise HTTPException(
            status_code=500,
            detail=_err("STORAGE_ERROR", "Failed to store uploaded file"),
        )

    # Update submission with actual file path
    from app.db.client import get_client
    get_client().table("coa_submissions").update({"file_path": file_path}).eq(
        "id", submission_id
    ).execute()

    # Queue background processing
    background_tasks.add_task(run_pipeline, submission_id, file_path, mime_type)

    logger.info("CoA upload accepted", submission_id=submission_id, filename=file.filename)

    return _ok({
        "submission_id": submission_id,
        "filename": file.filename,
        "status": SubmissionStatus.PENDING.value,
        "file_size_bytes": len(file_bytes),
    })


@router.get("/status/{submission_id}")
async def get_status(submission_id: str) -> dict[str, Any]:
    """Poll extraction status and page progress."""
    submission = await queries.get_submission(submission_id)
    if submission is None:
        raise HTTPException(
            status_code=404,
            detail=_err("NOT_FOUND", f"Submission {submission_id} not found"),
        )

    return _ok({
        "submission_id": submission_id,
        "status": submission["status"],
        "page_count": submission.get("page_count"),
        "pages_processed": submission.get("pages_processed", 0),
        "error_message": submission.get("error_message"),
    })


@router.get("/result/{submission_id}")
async def get_result(submission_id: str) -> dict[str, Any]:
    """Return full structured result with header, parameters, and validation."""
    submission = await queries.get_submission(submission_id)
    if submission is None:
        raise HTTPException(
            status_code=404,
            detail=_err("NOT_FOUND", f"Submission {submission_id} not found"),
        )

    if submission["status"] not in (
        SubmissionStatus.COMPLETED.value,
        SubmissionStatus.FAILED.value,
    ):
        raise HTTPException(
            status_code=409,
            detail=_err(
                "NOT_READY",
                f"Submission is still {submission['status']} — poll /status first",
            ),
        )

    extraction = await queries.get_extraction(submission_id)
    parameter_results = await queries.get_parameter_results(submission_id)

    # Compute overall status
    statuses = [r["validation_status"] for r in parameter_results]
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "ERROR" in statuses:
        overall = "ERROR"
    elif "WARNING" in statuses:
        overall = "WARNING"
    elif "REVIEW" in statuses:
        overall = "REVIEW"
    elif statuses:
        overall = "PASS"
    else:
        overall = "REVIEW"

    return _ok({
        "submission": {
            "id": submission["id"],
            "original_filename": submission["original_filename"],
            "status": submission["status"],
            "page_count": submission.get("page_count"),
            "created_at": submission.get("created_at"),
        },
        "header": {
            "product_name": extraction.get("product_name") if extraction else None,
            "product_grade": extraction.get("product_grade") if extraction else None,
            "supplier_name": extraction.get("supplier_name") if extraction else None,
            "batch_number": extraction.get("batch_number") if extraction else None,
            "manufacture_date": extraction.get("manufacture_date") if extraction else None,
            "expiry_date": extraction.get("expiry_date") if extraction else None,
            "coa_number": extraction.get("coa_number") if extraction else None,
            "header_confidence": extraction.get("header_confidence") if extraction else None,
            "extraction_notes": extraction.get("extraction_notes") if extraction else None,
        } if extraction else None,
        "parameters": parameter_results,
        "overall_status": overall,
        "parameter_count": len(parameter_results),
        "matched_product_id": submission.get("matched_product_id"),
    })


@router.get("/export/{submission_id}")
async def export_result(
    submission_id: str,
    format: str = Query(default="csv", pattern="^(csv|json)$"),
) -> Response:
    """Download CSV or JSON export of completed CoA analysis."""
    submission = await queries.get_submission(submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail=_err("NOT_FOUND", "Submission not found"))

    if submission["status"] != SubmissionStatus.COMPLETED.value:
        raise HTTPException(
            status_code=409,
            detail=_err("NOT_READY", "Export only available for completed submissions"),
        )

    try:
        file_bytes, filename, content_type = await generate_export(submission_id, format)
    except Exception as exc:
        logger.error("Export generation failed", submission_id=submission_id, exc_info=exc)
        raise HTTPException(
            status_code=500,
            detail=_err("EXPORT_ERROR", "Failed to generate export"),
        )

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/submissions")
async def list_submissions(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, Any]:
    """List recent submissions for the sidebar."""
    submissions = await queries.list_recent_submissions(limit=limit)
    return _ok(submissions)
