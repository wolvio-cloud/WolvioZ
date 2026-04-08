"""
CSV and JSON export generation for completed CoA submissions.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

import structlog

from app.db import queries

logger = structlog.get_logger(__name__)


async def generate_export(submission_id: str, format: str) -> tuple[bytes, str, str]:
    """
    Generate export for a completed submission.

    Returns: (file_bytes, filename, content_type)
    """
    submission = await queries.get_submission(submission_id)
    if submission is None:
        raise ValueError(f"Submission {submission_id} not found")

    extraction = await queries.get_extraction(submission_id)
    parameter_results = await queries.get_parameter_results(submission_id)

    if format == "csv":
        return _generate_csv(submission, extraction, parameter_results)
    elif format == "json":
        return _generate_json(submission, extraction, parameter_results)
    else:
        raise ValueError(f"Unsupported export format: {format}")


def _generate_csv(
    submission: dict[str, Any],
    extraction: dict[str, Any] | None,
    parameter_results: list[dict[str, Any]],
) -> tuple[bytes, str, str]:
    output = io.StringIO()
    writer = csv.writer(output)

    # Header block
    writer.writerow(["=== WOLVIO INTELLIGENCE — CoA AUDIT EXPORT ==="])
    writer.writerow(["Export Generated", datetime.now(timezone.utc).isoformat()])
    writer.writerow(["Submission ID", submission["id"]])
    writer.writerow(["Original File", submission["original_filename"]])
    writer.writerow(["Submission Date", submission["created_at"]])
    writer.writerow([])

    if extraction:
        writer.writerow(["=== DOCUMENT HEADER ==="])
        writer.writerow(["Product Name", extraction.get("product_name") or ""])
        writer.writerow(["Product Grade", extraction.get("product_grade") or ""])
        writer.writerow(["Supplier", extraction.get("supplier_name") or ""])
        writer.writerow(["Batch Number", extraction.get("batch_number") or ""])
        writer.writerow(["Manufacture Date", extraction.get("manufacture_date") or ""])
        writer.writerow(["Expiry Date", extraction.get("expiry_date") or ""])
        writer.writerow(["CoA Number", extraction.get("coa_number") or ""])
        writer.writerow(["Header Confidence", f"{extraction.get('header_confidence', 0):.2f}"])
        writer.writerow([])

    # Parameter table
    writer.writerow(["=== PARAMETER RESULTS ==="])
    writer.writerow([
        "Parameter Name",
        "Method Reference",
        "Result Value",
        "Unit",
        "Specification Limit",
        "CoA Pass/Fail",
        "Validation Status",
        "Margin from Boundary (%)",
        "Extraction Confidence",
        "Notes",
    ])

    for row in parameter_results:
        margin = row.get("margin_from_boundary")
        writer.writerow([
            row.get("parameter_name", ""),
            row.get("method_reference") or "",
            row.get("result_value", ""),
            row.get("result_unit") or "",
            row.get("specification_limit") or "",
            row.get("coa_pass_fail") or "",
            row.get("validation_status", ""),
            f"{margin:.2f}" if margin is not None else "",
            f"{row.get('extraction_confidence', 0):.2f}",
            row.get("validation_notes") or "",
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility
    filename = f"coa_audit_{submission['id'][:8]}_{_safe_batch(extraction)}.csv"
    return csv_bytes, filename, "text/csv"


def _generate_json(
    submission: dict[str, Any],
    extraction: dict[str, Any] | None,
    parameter_results: list[dict[str, Any]],
) -> tuple[bytes, str, str]:
    export_data = {
        "export_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "submission_id": submission["id"],
            "original_filename": submission["original_filename"],
            "submission_date": submission["created_at"],
            "export_format": "wolvio-coa-audit-v1",
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
        },
        "parameters": [
            {
                "parameter_name": r.get("parameter_name"),
                "method_reference": r.get("method_reference"),
                "result_value": r.get("result_value"),
                "result_unit": r.get("result_unit"),
                "specification_limit": r.get("specification_limit"),
                "coa_pass_fail": r.get("coa_pass_fail"),
                "validation_status": r.get("validation_status"),
                "margin_from_boundary_pct": r.get("margin_from_boundary"),
                "extraction_confidence": r.get("extraction_confidence"),
                "is_quantitative": r.get("is_quantitative"),
                "validation_notes": r.get("validation_notes"),
            }
            for r in parameter_results
        ],
        "summary": _compute_summary(parameter_results),
    }

    json_bytes = json.dumps(export_data, indent=2, default=str).encode("utf-8")
    filename = f"coa_audit_{submission['id'][:8]}_{_safe_batch(extraction)}.json"
    return json_bytes, filename, "application/json"


def _compute_summary(parameter_results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for r in parameter_results:
        status = r.get("validation_status", "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1

    total = len(parameter_results)
    overall = "PASS"
    if counts.get("FAIL", 0) > 0:
        overall = "FAIL"
    elif counts.get("ERROR", 0) > 0:
        overall = "ERROR"
    elif counts.get("WARNING", 0) > 0:
        overall = "WARNING"
    elif counts.get("REVIEW", 0) > 0:
        overall = "REVIEW"

    return {
        "total_parameters": total,
        "status_counts": counts,
        "overall_status": overall,
    }


def _safe_batch(extraction: dict[str, Any] | None) -> str:
    if not extraction:
        return "unknown"
    batch = extraction.get("batch_number") or "unknown"
    return batch.replace("/", "-").replace(" ", "_")[:20]
