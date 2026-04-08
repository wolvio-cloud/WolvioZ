"""
All database operations via Supabase async client.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.db.client import get_client
from app.db.models import SubmissionStatus, ValidationStatus

logger = structlog.get_logger(__name__)


# ─── Submissions ──────────────────────────────────────────────────────────────

async def create_submission(
    *,
    original_filename: str,
    file_path: str,
    file_size_bytes: int,
    mime_type: str,
) -> dict[str, Any]:
    client = get_client()
    submission_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    data = {
        "id": submission_id,
        "original_filename": original_filename,
        "file_path": file_path,
        "file_size_bytes": file_size_bytes,
        "mime_type": mime_type,
        "status": SubmissionStatus.PENDING.value,
        "pages_processed": 0,
        "created_at": now,
        "updated_at": now,
    }

    result = client.table("coa_submissions").insert(data).execute()
    return result.data[0]


async def update_submission_status(
    submission_id: str,
    *,
    status: SubmissionStatus,
    page_count: int | None = None,
    pages_processed: int | None = None,
    matched_product_id: str | None = None,
    error_message: str | None = None,
) -> None:
    client = get_client()
    payload: dict[str, Any] = {
        "status": status.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if page_count is not None:
        payload["page_count"] = page_count
    if pages_processed is not None:
        payload["pages_processed"] = pages_processed
    if matched_product_id is not None:
        payload["matched_product_id"] = matched_product_id
    if error_message is not None:
        payload["error_message"] = error_message

    client.table("coa_submissions").update(payload).eq("id", submission_id).execute()


async def get_submission(submission_id: str) -> dict[str, Any] | None:
    client = get_client()
    result = (
        client.table("coa_submissions")
        .select("*")
        .eq("id", submission_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def list_recent_submissions(limit: int = 20) -> list[dict[str, Any]]:
    client = get_client()
    result = (
        client.table("coa_submissions")
        .select("id,original_filename,status,created_at,matched_product_id")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


# ─── Extractions ──────────────────────────────────────────────────────────────

async def create_extraction(
    *,
    submission_id: str,
    product_name: str | None,
    product_grade: str | None,
    supplier_name: str | None,
    batch_number: str | None,
    manufacture_date: str | None,
    expiry_date: str | None,
    coa_number: str | None,
    header_confidence: float | None,
    raw_extraction_json: dict[str, Any],
    extraction_notes: str | None,
) -> dict[str, Any]:
    client = get_client()
    extraction_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    data = {
        "id": extraction_id,
        "submission_id": submission_id,
        "product_name": product_name,
        "product_grade": product_grade,
        "supplier_name": supplier_name,
        "batch_number": batch_number,
        "manufacture_date": manufacture_date,
        "expiry_date": expiry_date,
        "coa_number": coa_number,
        "header_confidence": header_confidence,
        "raw_extraction_json": raw_extraction_json,
        "extraction_notes": extraction_notes,
        "created_at": now,
    }

    result = client.table("coa_extractions").insert(data).execute()
    return result.data[0]


async def get_extraction(submission_id: str) -> dict[str, Any] | None:
    client = get_client()
    result = (
        client.table("coa_extractions")
        .select("*")
        .eq("submission_id", submission_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# ─── Parameter results ────────────────────────────────────────────────────────

async def create_parameter_results(
    submission_id: str, parameters: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    client = get_client()
    now = datetime.now(timezone.utc).isoformat()

    rows = [
        {
            "id": str(uuid.uuid4()),
            "submission_id": submission_id,
            "created_at": now,
            **param,
        }
        for param in parameters
    ]

    result = client.table("coa_parameter_results").insert(rows).execute()
    return result.data


async def get_parameter_results(submission_id: str) -> list[dict[str, Any]]:
    client = get_client()
    result = (
        client.table("coa_parameter_results")
        .select("*")
        .eq("submission_id", submission_id)
        .order("created_at")
        .execute()
    )
    return result.data


# ─── Products & Specs ─────────────────────────────────────────────────────────

async def get_all_products() -> list[dict[str, Any]]:
    client = get_client()
    result = client.table("products").select("*").execute()
    return result.data


async def get_spec_parameters_for_product(product_id: str) -> list[dict[str, Any]]:
    client = get_client()
    result = (
        client.table("spec_parameters")
        .select("*, spec_tables!inner(product_id)")
        .eq("spec_tables.product_id", product_id)
        .execute()
    )
    return result.data


async def upsert_product(
    name: str, grade: str | None, description: str | None
) -> dict[str, Any]:
    client = get_client()
    product_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    data = {
        "id": product_id,
        "name": name,
        "grade": grade,
        "description": description,
        "created_at": now,
    }

    result = (
        client.table("products")
        .upsert(data, on_conflict="name")
        .execute()
    )
    return result.data[0]


async def upsert_spec_table(
    product_id: str, version: str, effective_date: str | None
) -> dict[str, Any]:
    client = get_client()
    spec_table_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    data = {
        "id": spec_table_id,
        "product_id": product_id,
        "version": version,
        "effective_date": effective_date,
        "created_at": now,
    }

    result = (
        client.table("spec_tables")
        .upsert(data, on_conflict="product_id,version")
        .execute()
    )
    return result.data[0]


async def insert_spec_parameters(
    spec_table_id: str, parameters: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    client = get_client()
    now = datetime.now(timezone.utc).isoformat()

    rows = [
        {
            "id": str(uuid.uuid4()),
            "spec_table_id": spec_table_id,
            "created_at": now,
            **param,
        }
        for param in parameters
    ]

    result = client.table("spec_parameters").insert(rows).execute()
    return result.data
