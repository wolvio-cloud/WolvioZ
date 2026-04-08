"""
Validation comparator: compare extracted result against ParsedSpec to produce
one of 5 outcomes: PASS, WARNING, FAIL, REVIEW, ERROR.

5% warning band: if result is within spec but ≤5% of the nearest boundary, → WARNING.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.validation.spec_parser import ParsedSpec, SpecType
from app.db.models import ValidationStatus
from app.config import get_settings

settings = get_settings()

_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


@dataclass
class ValidationResult:
    status: ValidationStatus
    margin_from_boundary: float | None
    notes: str | None


def _extract_numeric(value: str) -> float | None:
    """Extract the first float from a string like '99.2%' or '1.25 mg/g'."""
    m = _NUMBER_RE.search(value)
    return float(m.group()) if m else None


def _compute_margin(value: float, spec: ParsedSpec) -> float | None:
    """
    Returns the percentage margin from the nearest spec boundary.
    margin = |value - boundary| / |boundary| * 100
    """
    boundaries: list[float] = []
    if spec.min_value is not None:
        boundaries.append(spec.min_value)
    if spec.max_value is not None:
        boundaries.append(spec.max_value)

    if not boundaries:
        return None

    margins = []
    for b in boundaries:
        if b == 0:
            margins.append(abs(value - b))
        else:
            margins.append(abs(value - b) / abs(b) * 100)

    return min(margins)


def validate_parameter(
    result_value: str,
    spec: ParsedSpec | None,
    extraction_confidence: float,
) -> ValidationResult:
    """
    Apply validation logic to a single extracted parameter.

    Priority order:
    1. ERROR  — if extraction_confidence < threshold
    2. REVIEW — if spec is None, or spec is QUALITATIVE/PASSES, or result is non-numeric
    3. FAIL   — if outside spec
    4. WARNING — if within spec but ≤5% from boundary
    5. PASS   — otherwise
    """
    threshold = settings.extraction_confidence_threshold
    warning_band = settings.extraction_warning_band_percent

    # 1. ERROR — low extraction confidence
    if extraction_confidence < threshold:
        return ValidationResult(
            status=ValidationStatus.ERROR,
            margin_from_boundary=None,
            notes=f"Extraction confidence {extraction_confidence:.2f} below threshold {threshold:.2f}",
        )

    # 2. REVIEW — no spec or qualitative spec
    if spec is None:
        return ValidationResult(
            status=ValidationStatus.REVIEW,
            margin_from_boundary=None,
            notes="No matching specification found",
        )

    if spec.spec_type in (SpecType.QUALITATIVE, SpecType.PASSES):
        return ValidationResult(
            status=ValidationStatus.REVIEW,
            margin_from_boundary=None,
            notes=f"Qualitative/passes spec — manual review required. Spec: {spec.raw_string}",
        )

    # Attempt numeric extraction
    numeric_value = _extract_numeric(result_value)
    if numeric_value is None:
        return ValidationResult(
            status=ValidationStatus.REVIEW,
            margin_from_boundary=None,
            notes=f"Non-numeric result value: '{result_value}'",
        )

    # 3. FAIL check
    if spec.spec_type == SpecType.MIN_ONLY and spec.min_value is not None:
        if spec.is_strict_lower:
            fails = numeric_value <= spec.min_value
        else:
            fails = numeric_value < spec.min_value
        if fails:
            margin = _compute_margin(numeric_value, spec)
            return ValidationResult(
                status=ValidationStatus.FAIL,
                margin_from_boundary=margin,
                notes=f"Result {numeric_value} below minimum {spec.min_value}",
            )

    elif spec.spec_type == SpecType.MAX_ONLY and spec.max_value is not None:
        if spec.is_strict_upper:
            fails = numeric_value >= spec.max_value
        else:
            fails = numeric_value > spec.max_value
        if fails:
            margin = _compute_margin(numeric_value, spec)
            return ValidationResult(
                status=ValidationStatus.FAIL,
                margin_from_boundary=margin,
                notes=f"Result {numeric_value} above maximum {spec.max_value}",
            )

    elif spec.spec_type == SpecType.RANGE:
        lo = spec.min_value
        hi = spec.max_value
        if lo is not None and hi is not None:
            if numeric_value < lo or numeric_value > hi:
                margin = _compute_margin(numeric_value, spec)
                return ValidationResult(
                    status=ValidationStatus.FAIL,
                    margin_from_boundary=margin,
                    notes=f"Result {numeric_value} outside range {lo}–{hi}",
                )

    # 4. WARNING — within spec but close to boundary
    margin = _compute_margin(numeric_value, spec)
    if margin is not None and margin <= warning_band:
        return ValidationResult(
            status=ValidationStatus.WARNING,
            margin_from_boundary=margin,
            notes=f"Within spec but {margin:.1f}% from boundary (warning band ≤{warning_band}%)",
        )

    # 5. PASS
    return ValidationResult(
        status=ValidationStatus.PASS,
        margin_from_boundary=margin,
        notes=None,
    )
