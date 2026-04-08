"""
Pydantic v2 models for the extraction JSON output from Claude/Gemini.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ExtractedHeader(BaseModel):
    product_name: str | None = None
    product_grade: str | None = None
    supplier_name: str | None = None
    batch_number: str | None = None
    manufacture_date: str | None = None
    expiry_date: str | None = None
    coa_number: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractedParameter(BaseModel):
    parameter_name: str
    method_reference: str | None = None
    result_value: str
    result_unit: str | None = None
    specification_limit: str | None = None
    coa_pass_fail: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    is_quantitative: bool = True

    @model_validator(mode="after")
    def strip_whitespace(self) -> "ExtractedParameter":
        self.parameter_name = self.parameter_name.strip()
        self.result_value = self.result_value.strip()
        return self


class ExtractionResult(BaseModel):
    header: ExtractedHeader
    parameters: list[ExtractedParameter] = Field(default_factory=list)
    extraction_notes: str | None = None
    page_index: int = 0
    model_used: str = "claude"
