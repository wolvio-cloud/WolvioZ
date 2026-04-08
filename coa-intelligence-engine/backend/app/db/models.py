"""
Pydantic models mirroring the Supabase database schema.

Tables:
  products              - Reference product catalogue
  spec_tables           - Specification document metadata
  spec_parameters       - Individual spec limits per product
  coa_submissions       - One row per uploaded CoA file
  coa_extractions       - AI extraction result per submission
  coa_parameter_results - Validated result per parameter
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class SubmissionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    ERROR = "ERROR"


# ─── Reference data ───────────────────────────────────────────────────────────

class Product(BaseModel):
    id: UUID
    name: str
    grade: str | None = None
    description: str | None = None
    created_at: datetime


class SpecTable(BaseModel):
    id: UUID
    product_id: UUID
    version: str
    effective_date: str | None = None
    created_at: datetime


class SpecParameter(BaseModel):
    id: UUID
    spec_table_id: UUID
    parameter_name: str
    method_reference: str | None = None
    specification_limit: str
    is_quantitative: bool = True
    created_at: datetime


# ─── Transactional data ───────────────────────────────────────────────────────

class CoASubmission(BaseModel):
    id: UUID
    original_filename: str
    file_path: str
    file_size_bytes: int
    mime_type: str
    status: SubmissionStatus
    page_count: int | None = None
    pages_processed: int = 0
    matched_product_id: UUID | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class CoAExtraction(BaseModel):
    id: UUID
    submission_id: UUID
    product_name: str | None = None
    product_grade: str | None = None
    supplier_name: str | None = None
    batch_number: str | None = None
    manufacture_date: str | None = None
    expiry_date: str | None = None
    coa_number: str | None = None
    header_confidence: float | None = None
    raw_extraction_json: dict[str, Any]
    extraction_notes: str | None = None
    created_at: datetime


class CoAParameterResult(BaseModel):
    id: UUID
    submission_id: UUID
    parameter_name: str
    method_reference: str | None = None
    result_value: str
    result_unit: str | None = None
    specification_limit: str | None = None
    coa_pass_fail: str | None = None
    extraction_confidence: float
    validation_status: ValidationStatus
    margin_from_boundary: float | None = None
    spec_parameter_id: UUID | None = None
    is_quantitative: bool = True
    validation_notes: str | None = None
    created_at: datetime
