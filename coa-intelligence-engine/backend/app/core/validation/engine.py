"""
Validation engine: orchestrates product matching, spec lookup, and parameter validation.
"""
from __future__ import annotations

import structlog

from app.core.extraction.schemas import ExtractionResult, ExtractedParameter
from app.core.validation.matcher import match_product
from app.core.validation.spec_parser import parse_spec_limit, SpecType
from app.core.validation.comparator import validate_parameter
from app.db.models import ValidationStatus
from app.db import queries

logger = structlog.get_logger(__name__)


async def run_validation(
    extraction: ExtractionResult,
    submission_id: str,
) -> tuple[str | None, list[dict]]:
    """
    Match product, fetch spec, validate every parameter.

    Returns:
        (matched_product_id | None, list of parameter result dicts ready for DB insert)
    """
    # 1. Load all products for matching
    products = await queries.get_all_products()
    matched_product_id, match_score = match_product(
        extraction.header.product_name, products
    )

    # 2. Load spec parameters if product matched
    spec_map: dict[str, dict] = {}  # normalised_name → spec_param row
    if matched_product_id:
        spec_rows = await queries.get_spec_parameters_for_product(matched_product_id)
        for row in spec_rows:
            key = row["parameter_name"].lower().strip()
            spec_map[key] = row

    parameter_results: list[dict] = []

    for param in extraction.parameters:
        key = param.parameter_name.lower().strip()
        spec_row = spec_map.get(key)

        parsed_spec = None
        spec_param_id = None
        if spec_row:
            parsed_spec = parse_spec_limit(spec_row.get("specification_limit", ""))
            spec_param_id = str(spec_row.get("id", ""))
        elif param.specification_limit:
            # Use spec from CoA itself if no internal spec available
            parsed_spec = parse_spec_limit(param.specification_limit)

        result = validate_parameter(
            result_value=param.result_value,
            spec=parsed_spec,
            extraction_confidence=param.confidence,
        )

        parameter_results.append({
            "submission_id": submission_id,
            "parameter_name": param.parameter_name,
            "method_reference": param.method_reference,
            "result_value": param.result_value,
            "result_unit": param.result_unit,
            "specification_limit": (
                spec_row["specification_limit"] if spec_row
                else param.specification_limit
            ),
            "coa_pass_fail": param.coa_pass_fail,
            "extraction_confidence": param.confidence,
            "validation_status": result.status.value,
            "margin_from_boundary": result.margin_from_boundary,
            "spec_parameter_id": spec_param_id,
            "is_quantitative": param.is_quantitative,
            "validation_notes": result.notes,
        })

    counts = {}
    for r in parameter_results:
        counts[r["validation_status"]] = counts.get(r["validation_status"], 0) + 1

    logger.info(
        "Validation complete",
        submission_id=submission_id,
        matched_product=matched_product_id,
        match_score=match_score,
        parameter_counts=counts,
    )

    return matched_product_id, parameter_results
