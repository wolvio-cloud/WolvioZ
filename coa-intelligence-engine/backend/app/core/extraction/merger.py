"""
Multi-page result merger: combine ExtractionResult objects from all pages
into one unified result, deduplicating parameters by name.
"""
from __future__ import annotations

import structlog
from app.core.extraction.schemas import ExtractionResult, ExtractedHeader, ExtractedParameter

logger = structlog.get_logger(__name__)


def _normalise_name(name: str) -> str:
    return name.lower().strip().replace("  ", " ")


def merge_page_results(page_results: list[ExtractionResult]) -> ExtractionResult:
    """
    Merge multiple per-page ExtractionResult objects into one.

    Header: use the page with highest header confidence.
    Parameters: union of all pages, deduplicated by normalised parameter_name.
                When duplicate, keep the one with higher confidence.
    Notes: concatenate non-null notes separated by ' | '.
    """
    if not page_results:
        raise ValueError("No page results to merge")

    if len(page_results) == 1:
        return page_results[0]

    # Pick best header
    best_header_result = max(page_results, key=lambda r: r.header.confidence)
    merged_header = best_header_result.header

    # If some header fields are null but present in other pages, fill them in
    for result in page_results:
        h = result.header
        if merged_header.product_name is None and h.product_name:
            merged_header = merged_header.model_copy(update={"product_name": h.product_name})
        if merged_header.supplier_name is None and h.supplier_name:
            merged_header = merged_header.model_copy(update={"supplier_name": h.supplier_name})
        if merged_header.batch_number is None and h.batch_number:
            merged_header = merged_header.model_copy(update={"batch_number": h.batch_number})
        if merged_header.coa_number is None and h.coa_number:
            merged_header = merged_header.model_copy(update={"coa_number": h.coa_number})
        if merged_header.manufacture_date is None and h.manufacture_date:
            merged_header = merged_header.model_copy(update={"manufacture_date": h.manufacture_date})
        if merged_header.expiry_date is None and h.expiry_date:
            merged_header = merged_header.model_copy(update={"expiry_date": h.expiry_date})

    # Deduplicate parameters
    seen: dict[str, ExtractedParameter] = {}
    for result in page_results:
        for param in result.parameters:
            key = _normalise_name(param.parameter_name)
            existing = seen.get(key)
            if existing is None or param.confidence > existing.confidence:
                seen[key] = param

    merged_parameters = list(seen.values())

    # Merge notes
    notes_parts = [r.extraction_notes for r in page_results if r.extraction_notes]
    merged_notes = " | ".join(notes_parts) if notes_parts else None

    # Model used — pick the most common
    model_counts: dict[str, int] = {}
    for r in page_results:
        model_counts[r.model_used] = model_counts.get(r.model_used, 0) + 1
    primary_model = max(model_counts, key=lambda k: model_counts[k])

    logger.info(
        "Pages merged",
        total_pages=len(page_results),
        total_parameters=len(merged_parameters),
        model=primary_model,
    )

    return ExtractionResult(
        header=merged_header,
        parameters=merged_parameters,
        extraction_notes=merged_notes,
        page_index=0,
        model_used=primary_model,
    )
