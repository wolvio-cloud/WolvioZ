"""
Main pipeline orchestrator: intake → extract → validate → store.

Called as a FastAPI BackgroundTask after the upload endpoint returns.
"""
from __future__ import annotations

import asyncio
import structlog

from app.core.extraction.intake import render_to_pages
from app.core.extraction.vision import extract_page
from app.core.extraction.merger import merge_page_results
from app.core.extraction.schemas import ExtractionResult
from app.core.validation.engine import run_validation
from app.db import queries
from app.db.models import SubmissionStatus
from app.storage.files import download_coa_file

logger = structlog.get_logger(__name__)


async def run_pipeline(submission_id: str, file_path: str, mime_type: str) -> None:
    """
    Full extraction + validation pipeline for one CoA submission.

    Steps:
    1. Download file from Supabase Storage
    2. Render all pages to PNG at 200 DPI
    3. Extract data from all pages concurrently
    4. Merge multi-page results
    5. Validate extracted parameters against internal specs
    6. Persist everything to Supabase
    """
    log = logger.bind(submission_id=submission_id)

    try:
        # 1. Update status → processing
        await queries.update_submission_status(
            submission_id, status=SubmissionStatus.PROCESSING
        )
        log.info("Pipeline started")

        # 2. Download raw file
        file_bytes = await download_coa_file(file_path)
        log.info("File downloaded", size=len(file_bytes))

        # 3. Render to pages
        pages = await render_to_pages(file_bytes, mime_type)
        total_pages = len(pages)
        log.info("Pages rendered", total_pages=total_pages)

        await queries.update_submission_status(
            submission_id,
            status=SubmissionStatus.PROCESSING,
            page_count=total_pages,
            pages_processed=0,
        )

        # 4. Concurrent extraction — asyncio.gather over all pages
        semaphore = asyncio.Semaphore(3)  # max 3 concurrent API calls

        async def extract_with_progress(page_index: int, png_bytes: bytes) -> ExtractionResult:
            async with semaphore:
                result = await extract_page(png_bytes, page_index, total_pages)
                await queries.update_submission_status(
                    submission_id,
                    status=SubmissionStatus.PROCESSING,
                    pages_processed=page_index + 1,
                )
                return result

        page_results = await asyncio.gather(
            *[extract_with_progress(idx, png) for idx, png in pages],
            return_exceptions=True,
        )

        # Filter out any failed pages
        valid_results: list[ExtractionResult] = []
        for i, res in enumerate(page_results):
            if isinstance(res, Exception):
                log.error("Page extraction failed", page=i, exc_info=res)
            else:
                valid_results.append(res)

        if not valid_results:
            raise RuntimeError("All page extractions failed")

        # 5. Merge pages
        merged = merge_page_results(valid_results)
        log.info("Extraction merged", parameters=len(merged.parameters))

        # 6. Persist extraction
        await queries.create_extraction(
            submission_id=submission_id,
            product_name=merged.header.product_name,
            product_grade=merged.header.product_grade,
            supplier_name=merged.header.supplier_name,
            batch_number=merged.header.batch_number,
            manufacture_date=merged.header.manufacture_date,
            expiry_date=merged.header.expiry_date,
            coa_number=merged.header.coa_number,
            header_confidence=merged.header.confidence,
            raw_extraction_json=merged.model_dump(),
            extraction_notes=merged.extraction_notes,
        )

        # 7. Validate
        matched_product_id, parameter_results = await run_validation(merged, submission_id)

        # 8. Persist parameter results
        if parameter_results:
            await queries.create_parameter_results(submission_id, parameter_results)

        # 9. Mark completed
        await queries.update_submission_status(
            submission_id,
            status=SubmissionStatus.COMPLETED,
            pages_processed=total_pages,
            matched_product_id=matched_product_id,
        )
        log.info("Pipeline completed", matched_product=matched_product_id)

    except Exception as exc:
        log.error("Pipeline failed", exc_info=exc)
        try:
            await queries.update_submission_status(
                submission_id,
                status=SubmissionStatus.FAILED,
                error_message=str(exc),
            )
        except Exception as inner_exc:
            log.error("Failed to update submission status after failure", exc_info=inner_exc)
