"""
Unit tests for extraction schemas and merger logic.
"""
import pytest
from app.core.extraction.schemas import ExtractionResult, ExtractedHeader, ExtractedParameter
from app.core.extraction.merger import merge_page_results


def _make_result(
    product_name=None,
    supplier_name=None,
    batch_number=None,
    header_confidence=0.8,
    parameters=None,
    page_index=0,
    model_used="claude",
    notes=None,
) -> ExtractionResult:
    return ExtractionResult(
        header=ExtractedHeader(
            product_name=product_name,
            supplier_name=supplier_name,
            batch_number=batch_number,
            confidence=header_confidence,
        ),
        parameters=parameters or [],
        extraction_notes=notes,
        page_index=page_index,
        model_used=model_used,
    )


def _make_param(name: str, value: str, confidence: float = 0.9) -> ExtractedParameter:
    return ExtractedParameter(
        parameter_name=name,
        result_value=value,
        confidence=confidence,
    )


# ─── Schema validation ────────────────────────────────────────────────────────

def test_extraction_result_defaults():
    result = _make_result()
    assert result.parameters == []
    assert result.extraction_notes is None
    assert result.model_used == "claude"


def test_parameter_strips_whitespace():
    param = ExtractedParameter(
        parameter_name="  Assay  ",
        result_value="  99.2%  ",
        confidence=0.9,
    )
    assert param.parameter_name == "Assay"
    assert param.result_value == "99.2%"


def test_parameter_confidence_bounds():
    with pytest.raises(Exception):
        ExtractedParameter(
            parameter_name="Assay",
            result_value="99%",
            confidence=1.5,  # > 1.0 — should fail
        )


def test_parameter_is_quantitative_default():
    param = _make_param("Assay", "99%")
    assert param.is_quantitative is True


# ─── Merger ───────────────────────────────────────────────────────────────────

def test_merge_single_page():
    r = _make_result(
        product_name="Paracetamol IP",
        parameters=[_make_param("Assay", "99.2%")],
    )
    merged = merge_page_results([r])
    assert merged.header.product_name == "Paracetamol IP"
    assert len(merged.parameters) == 1


def test_merge_picks_highest_header_confidence():
    r1 = _make_result(product_name="Product A", header_confidence=0.7, page_index=0)
    r2 = _make_result(product_name="Product B", header_confidence=0.9, page_index=1)
    merged = merge_page_results([r1, r2])
    assert merged.header.product_name == "Product B"


def test_merge_fills_null_header_fields():
    r1 = _make_result(product_name="Paracetamol", supplier_name=None, header_confidence=0.9)
    r2 = _make_result(product_name=None, supplier_name="Supplier X", header_confidence=0.7)
    merged = merge_page_results([r1, r2])
    assert merged.header.product_name == "Paracetamol"
    assert merged.header.supplier_name == "Supplier X"


def test_merge_deduplicates_parameters():
    r1 = _make_result(parameters=[_make_param("Assay", "99.0%", confidence=0.7)])
    r2 = _make_result(parameters=[_make_param("Assay", "99.2%", confidence=0.9)])
    merged = merge_page_results([r1, r2])
    assert len(merged.parameters) == 1
    assert merged.parameters[0].result_value == "99.2%"  # higher confidence wins


def test_merge_dedup_case_insensitive():
    r1 = _make_result(parameters=[_make_param("assay", "99.0%")])
    r2 = _make_result(parameters=[_make_param("ASSAY", "99.2%", confidence=0.95)])
    merged = merge_page_results([r1, r2])
    assert len(merged.parameters) == 1


def test_merge_combines_all_unique_parameters():
    r1 = _make_result(parameters=[_make_param("Assay", "99%"), _make_param("pH", "5.5")])
    r2 = _make_result(parameters=[_make_param("Moisture", "0.3%"), _make_param("Residue", "0.1%")])
    merged = merge_page_results([r1, r2])
    assert len(merged.parameters) == 4


def test_merge_concatenates_notes():
    r1 = _make_result(notes="Page 1 note")
    r2 = _make_result(notes="Page 2 note")
    merged = merge_page_results([r1, r2])
    assert "Page 1 note" in merged.extraction_notes
    assert "Page 2 note" in merged.extraction_notes


def test_merge_empty_notes_ignored():
    r1 = _make_result(notes=None)
    r2 = _make_result(notes="Some note")
    merged = merge_page_results([r1, r2])
    assert merged.extraction_notes == "Some note"


def test_merge_raises_on_empty_list():
    with pytest.raises(ValueError):
        merge_page_results([])
