"""
Unit tests for spec_parser.py — 25+ cases covering all 5 spec types and edge cases.
"""
import pytest
from app.core.validation.spec_parser import parse_spec_limit, SpecType, ParsedSpec


# ─── MIN_ONLY ─────────────────────────────────────────────────────────────────

def test_min_only_nlt_with_percent():
    spec = parse_spec_limit("NLT 98.0%")
    assert spec.spec_type == SpecType.MIN_ONLY
    assert spec.min_value == 98.0
    assert spec.unit == "%"
    assert spec.is_strict_lower is False


def test_min_only_nlt_lowercase():
    spec = parse_spec_limit("nlt 97.5%")
    assert spec.spec_type == SpecType.MIN_ONLY
    assert spec.min_value == 97.5


def test_min_only_not_less_than():
    spec = parse_spec_limit("Not less than 98.0%")
    assert spec.spec_type == SpecType.MIN_ONLY
    assert spec.min_value == 98.0


def test_min_only_gte_symbol():
    spec = parse_spec_limit("≥ 98.0%")
    assert spec.spec_type == SpecType.MIN_ONLY
    assert spec.min_value == 98.0
    assert spec.is_strict_lower is False


def test_min_only_ascii_gte():
    spec = parse_spec_limit(">= 99.0")
    assert spec.spec_type == SpecType.MIN_ONLY
    assert spec.min_value == 99.0


def test_min_only_strict_gt():
    spec = parse_spec_limit("> 0.5")
    assert spec.spec_type == SpecType.MIN_ONLY
    assert spec.min_value == 0.5
    assert spec.is_strict_lower is True


def test_min_only_no_unit():
    spec = parse_spec_limit("NLT 99")
    assert spec.spec_type == SpecType.MIN_ONLY
    assert spec.min_value == 99.0
    assert spec.unit is None


# ─── MAX_ONLY ─────────────────────────────────────────────────────────────────

def test_max_only_nmt_with_percent():
    spec = parse_spec_limit("NMT 0.5%")
    assert spec.spec_type == SpecType.MAX_ONLY
    assert spec.max_value == 0.5
    assert spec.unit == "%"
    assert spec.is_strict_upper is False


def test_max_only_not_more_than():
    spec = parse_spec_limit("Not more than 0.5%")
    assert spec.spec_type == SpecType.MAX_ONLY
    assert spec.max_value == 0.5


def test_max_only_lte_symbol():
    spec = parse_spec_limit("≤ 0.1%")
    assert spec.spec_type == SpecType.MAX_ONLY
    assert spec.max_value == 0.1
    assert spec.is_strict_upper is False


def test_max_only_strict_lt():
    spec = parse_spec_limit("<0.01%")
    assert spec.spec_type == SpecType.MAX_ONLY
    assert spec.max_value == 0.01
    assert spec.is_strict_upper is True


def test_max_only_ascii_lte():
    spec = parse_spec_limit("<= 0.5%")
    assert spec.spec_type == SpecType.MAX_ONLY
    assert spec.max_value == 0.5


def test_max_only_nmt_ppm():
    spec = parse_spec_limit("NMT 10 ppm")
    assert spec.spec_type == SpecType.MAX_ONLY
    assert spec.max_value == 10.0


# ─── RANGE ────────────────────────────────────────────────────────────────────

def test_range_dash():
    spec = parse_spec_limit("98.0 - 102.0%")
    assert spec.spec_type == SpecType.RANGE
    assert spec.min_value == 98.0
    assert spec.max_value == 102.0
    assert spec.unit == "%"


def test_range_en_dash():
    spec = parse_spec_limit("98.0–102.0%")
    assert spec.spec_type == SpecType.RANGE
    assert spec.min_value == 98.0
    assert spec.max_value == 102.0


def test_range_to_keyword():
    spec = parse_spec_limit("2.0 to 3.0%")
    assert spec.spec_type == SpecType.RANGE
    assert spec.min_value == 2.0
    assert spec.max_value == 3.0


def test_range_no_unit():
    spec = parse_spec_limit("4.5 - 5.5")
    assert spec.spec_type == SpecType.RANGE
    assert spec.min_value == 4.5
    assert spec.max_value == 5.5
    assert spec.unit is None


def test_range_integers():
    spec = parse_spec_limit("5 - 7")
    assert spec.spec_type == SpecType.RANGE
    assert spec.min_value == 5.0
    assert spec.max_value == 7.0


# ─── QUALITATIVE ──────────────────────────────────────────────────────────────

def test_qualitative_appearance():
    spec = parse_spec_limit("White crystalline powder")
    assert spec.spec_type == SpecType.QUALITATIVE
    assert spec.min_value is None
    assert spec.max_value is None


def test_qualitative_colour():
    spec = parse_spec_limit("Clear colourless liquid")
    assert spec.spec_type == SpecType.QUALITATIVE


def test_qualitative_odour():
    spec = parse_spec_limit("Characteristic odour")
    assert spec.spec_type == SpecType.QUALITATIVE


def test_qualitative_empty():
    spec = parse_spec_limit("")
    assert spec.spec_type == SpecType.QUALITATIVE


# ─── PASSES ───────────────────────────────────────────────────────────────────

def test_passes_passes_test():
    spec = parse_spec_limit("Passes test")
    assert spec.spec_type == SpecType.PASSES


def test_passes_conforms():
    spec = parse_spec_limit("Conforms")
    assert spec.spec_type == SpecType.PASSES


def test_passes_complies():
    spec = parse_spec_limit("Complies")
    assert spec.spec_type == SpecType.PASSES


def test_passes_case_insensitive():
    spec = parse_spec_limit("PASSES TEST")
    assert spec.spec_type == SpecType.PASSES


# ─── Raw string preserved ─────────────────────────────────────────────────────

def test_raw_string_preserved():
    raw = "NLT 98.0%"
    spec = parse_spec_limit(raw)
    assert spec.raw_string == raw


def test_range_raw_string_preserved():
    raw = "98.0 - 102.0%"
    spec = parse_spec_limit(raw)
    assert spec.raw_string == raw
