"""
Spec seeding endpoint: POST /api/specs/parameters
Admin endpoint to bulk-insert spec parameters for a product.
"""
from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import queries

router = APIRouter()
logger = structlog.get_logger(__name__)


def _ok(data: Any) -> dict[str, Any]:
    return {"data": data, "error": None}


def _err(code: str, message: str) -> dict[str, Any]:
    return {"data": None, "error": {"code": code, "message": message}}


class SpecParameterIn(BaseModel):
    parameter_name: str = Field(..., min_length=1)
    method_reference: str | None = None
    specification_limit: str = Field(..., min_length=1)
    is_quantitative: bool = True


class SeedSpecsRequest(BaseModel):
    product_name: str = Field(..., min_length=1)
    product_grade: str | None = None
    product_description: str | None = None
    spec_version: str = Field(default="v1.0")
    effective_date: str | None = None
    parameters: list[SpecParameterIn] = Field(..., min_length=1)


@router.post("/parameters", status_code=201)
async def seed_spec_parameters(body: SeedSpecsRequest) -> dict[str, Any]:
    """
    Upsert a product with its spec table and all parameters.
    Idempotent: re-running with the same product_name + spec_version replaces parameters.
    """
    # Upsert product
    product = await queries.upsert_product(
        body.product_name,
        body.product_grade,
        body.product_description,
    )
    product_id = str(product["id"])

    # Upsert spec table
    spec_table = await queries.upsert_spec_table(
        product_id, body.spec_version, body.effective_date
    )
    spec_table_id = str(spec_table["id"])

    # Insert parameters
    param_rows = [
        {
            "parameter_name": p.parameter_name,
            "method_reference": p.method_reference,
            "specification_limit": p.specification_limit,
            "is_quantitative": p.is_quantitative,
        }
        for p in body.parameters
    ]

    inserted = await queries.insert_spec_parameters(spec_table_id, param_rows)

    logger.info(
        "Spec parameters seeded",
        product=body.product_name,
        version=body.spec_version,
        count=len(inserted),
    )

    return _ok({
        "product_id": product_id,
        "spec_table_id": spec_table_id,
        "parameters_inserted": len(inserted),
    })
