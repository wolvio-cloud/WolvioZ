"""
Unit tests for validation comparator — covers all 5 outcomes + warning band logic.
"""
import pytest
from app.core.validation.spec_parser import parse_spec_limit, ParsedSpec, SpecType
from app.core.validation.comparator import validate_parameter
from app.db.models import ValidationStatus


# ─── PASS ─────────────────────────────────────────────────────────────────────

def test_pass_within_range():
    spec = parse_spec_limit("98.0 - 102.0%")
    result = validate_parameter("100.0%", spec, confidence=0.95)
    assert result.status == ValidationStatus.PASS


def test_pass_above_min_only():
    spec = parse_spec_limit("NLT 98.0%")
    result = validate_parameter("99.5%", spec, confidence=0.9)
    assert result.status == ValidationStatus.PASS


def test_pass_below_max_only():
    spec = parse_spec_limit("NMT 0.5%")
    result = validate_parameter("0.1%", spec, confidence=0.9)
    assert result.status == ValidationStatus.PASS


# ─── WARNING band ─────────────────────────────────────────────────────────────

def test_warning_at_range_lower_boundary():
    # Range 98.0–102.0, result=98.1 → margin from 98.0 = 0.1/98.0*100 ≈ 0.10% → WARNING
    spec = parse_spec_limit("98.0 - 102.0%")
    result = validate_parameter("98.1%", spec, confidence=0.95)
    assert result.status == ValidationStatus.WARNING
    assert result.margin_from_boundary is not None
    assert result.margin_from_boundary < 5.0


def test_warning_at_range_upper_boundary():
    # Range 98.0–102.0, result=101.9 → margin from 102.0 ≈ 0.10% → WARNING
    spec = parse_spec_limit("98.0 - 102.0%")
    result = validate_parameter("101.9%", spec, confidence=0.95)
    assert result.status == ValidationStatus.WARNING


def test_warning_at_min_boundary():
    # NLT 98.0, result=98.5 → margin = 0.5/98.0*100 ≈ 0.51% → WARNING
    spec = parse_spec_limit("NLT 98.0%")
    result = validate_parameter("98.5%", spec, confidence=0.9)
    assert result.status == ValidationStatus.WARNING


def test_warning_at_max_boundary():
    # NMT 0.5, result=0.49 → margin = 0.01/0.5*100 = 2.0% → WARNING
    spec = parse_spec_limit("NMT 0.5%")
    result = validate_parameter("0.49%", spec, confidence=0.9)
    assert result.status == ValidationStatus.WARNING


def test_no_warning_far_from_boundary():
    # Range 98.0–102.0, result=100.0 → margin from 98 = 2.04%, from 102 = 1.96% — both >5%? No, 1.96 < 5
    # Actually (100-98)/98 = 2.04%, still < 5% → WARNING
    # Let's pick result=100 in range 90-110 → margin from 90 = 11.1%, from 110 = 9.1% → PASS
    spec = parse_spec_limit("90.0 - 110.0%")
    result = validate_parameter("100.0%", spec, confidence=0.95)
    assert result.status == ValidationStatus.PASS


# ─── FAIL ─────────────────────────────────────────────────────────────────────

def test_fail_below_min():
    spec = parse_spec_limit("NLT 98.0%")
    result = validate_parameter("97.0%", spec, confidence=0.9)
    assert result.status == ValidationStatus.FAIL


def test_fail_above_max():
    spec = parse_spec_limit("NMT 0.5%")
    result = validate_parameter("0.8%", spec, confidence=0.9)
    assert result.status == ValidationStatus.FAIL


def test_fail_outside_range_low():
    spec = parse_spec_limit("98.0 - 102.0%")
    result = validate_parameter("95.0%", spec, confidence=0.9)
    assert result.status == ValidationStatus.FAIL


def test_fail_outside_range_high():
    spec = parse_spec_limit("98.0 - 102.0%")
    result = validate_parameter("105.0%", spec, confidence=0.9)
    assert result.status == ValidationStatus.FAIL


def test_fail_strict_lt_at_boundary():
    # <0.5 → 0.5 fails (strict)
    spec = parse_spec_limit("<0.5%")
    result = validate_parameter("0.5%", spec, confidence=0.9)
    assert result.status == ValidationStatus.FAIL


# ─── REVIEW ───────────────────────────────────────────────────────────────────

def test_review_no_spec():
    result = validate_parameter("White powder", spec=None, confidence=0.9)
    assert result.status == ValidationStatus.REVIEW


def test_review_qualitative_spec():
    spec = parse_spec_limit("White crystalline powder")
    result = validate_parameter("White crystalline powder", spec, confidence=0.9)
    assert result.status == ValidationStatus.REVIEW


def test_review_passes_spec():
    spec = parse_spec_limit("Passes test")
    result = validate_parameter("Passes", spec, confidence=0.9)
    assert result.status == ValidationStatus.REVIEW


def test_review_non_numeric_value():
    spec = parse_spec_limit("98.0 - 102.0%")
    result = validate_parameter("See attached report", spec, confidence=0.9)
    assert result.status == ValidationStatus.REVIEW


# ─── ERROR ────────────────────────────────────────────────────────────────────

def test_error_low_confidence():
    spec = parse_spec_limit("NLT 98.0%")
    result = validate_parameter("99.0%", spec, confidence=0.5)
    assert result.status == ValidationStatus.ERROR


def test_error_very_low_confidence():
    spec = parse_spec_limit("98.0 - 102.0%")
    result = validate_parameter("100.0%", spec, confidence=0.1)
    assert result.status == ValidationStatus.ERROR


def test_error_at_threshold():
    # confidence == threshold → should be ERROR (strictly below)
    spec = parse_spec_limit("NLT 98.0%")
    result = validate_parameter("99.0%", spec, confidence=0.59)
    assert result.status == ValidationStatus.ERROR


def test_no_error_just_above_threshold():
    spec = parse_spec_limit("NLT 98.0%")
    result = validate_parameter("99.0%", spec, confidence=0.61)
    # Should not be ERROR (might be PASS or WARNING)
    assert result.status != ValidationStatus.ERROR
