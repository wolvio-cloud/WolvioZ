"""
Spec limit parser: converts raw specification strings into ParsedSpec dataclasses.

Handles 5 spec types:
  MIN_ONLY  : "NLT 98.0%", "≥ 98.0", "Not less than 98.0%"
  MAX_ONLY  : "NMT 0.5%", "≤ 0.5%", "<0.1%", "Not more than 0.5%"
  RANGE     : "98.0 - 102.0%", "2.0 to 3.0", "98.0–102.0"
  QUALITATIVE: "White crystalline powder", "Clear colourless liquid"
  PASSES    : "Passes test", "Conforms", "Complies"
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class SpecType(str, Enum):
    MIN_ONLY = "MIN_ONLY"
    MAX_ONLY = "MAX_ONLY"
    RANGE = "RANGE"
    QUALITATIVE = "QUALITATIVE"
    PASSES = "PASSES"


@dataclass
class ParsedSpec:
    spec_type: SpecType
    min_value: float | None
    max_value: float | None
    unit: str | None
    raw_string: str
    is_strict_lower: bool = False  # True means > (not ≥)
    is_strict_upper: bool = False  # True means < (not ≤)


# ─── Regex patterns ───────────────────────────────────────────────────────────

_NUMBER = r"(\d+(?:\.\d+)?)"
_UNIT = r"([%\w/μµ°]+(?:\s*\w+/\w+)?)?(?:\s*)?"

# MIN_ONLY patterns
_RE_NLT = re.compile(
    r"(?:NLT|not\s+less\s+than|≥|>=)\s*" + _NUMBER + r"\s*" + _UNIT,
    re.IGNORECASE,
)
_RE_GT_STRICT = re.compile(
    r"(?:>)\s*" + _NUMBER + r"\s*" + _UNIT,
    re.IGNORECASE,
)

# MAX_ONLY patterns
_RE_NMT = re.compile(
    r"(?:NMT|not\s+more\s+than|≤|<=)\s*" + _NUMBER + r"\s*" + _UNIT,
    re.IGNORECASE,
)
_RE_LT_STRICT = re.compile(
    r"(?:<)\s*" + _NUMBER + r"\s*" + _UNIT,
    re.IGNORECASE,
)
_RE_MAX_ONLY_LABEL = re.compile(
    r"(?:maximum|max\.?)\s*:?\s*" + _NUMBER + r"\s*" + _UNIT,
    re.IGNORECASE,
)

# RANGE patterns
_RE_RANGE_DASH = re.compile(
    _NUMBER + r"\s*(?:–|-|to)\s*" + _NUMBER + r"\s*" + _UNIT,
    re.IGNORECASE,
)

# PASSES patterns
_PASSES_KEYWORDS = re.compile(
    r"^\s*(?:passes?\s+test|conforms?|complies?|compliant)\s*$",
    re.IGNORECASE,
)


def _extract_unit(raw_unit: str | None) -> str | None:
    if not raw_unit:
        return None
    unit = raw_unit.strip()
    if not unit:
        return None
    # Reject units that are just stray words that aren't real units
    non_units = {"test", "specification", "limit", "method", "reference"}
    if unit.lower() in non_units:
        return None
    return unit


def parse_spec_limit(raw_string: str) -> ParsedSpec:
    """
    Parse a raw spec limit string into a ParsedSpec dataclass.

    Returns a QUALITATIVE spec if the string cannot be parsed as numeric.
    """
    s = raw_string.strip()

    if not s:
        return ParsedSpec(
            spec_type=SpecType.QUALITATIVE,
            min_value=None,
            max_value=None,
            unit=None,
            raw_string=raw_string,
        )

    # PASSES
    if _PASSES_KEYWORDS.match(s):
        return ParsedSpec(
            spec_type=SpecType.PASSES,
            min_value=None,
            max_value=None,
            unit=None,
            raw_string=raw_string,
        )

    # RANGE (must come before MIN/MAX to catch "98.0 - 102.0%")
    m = _RE_RANGE_DASH.match(s)
    if m:
        lo, hi, unit = m.group(1), m.group(2), m.group(3)
        return ParsedSpec(
            spec_type=SpecType.RANGE,
            min_value=float(lo),
            max_value=float(hi),
            unit=_extract_unit(unit),
            raw_string=raw_string,
        )

    # MIN_ONLY — NLT / ≥
    m = _RE_NLT.match(s)
    if m:
        return ParsedSpec(
            spec_type=SpecType.MIN_ONLY,
            min_value=float(m.group(1)),
            max_value=None,
            unit=_extract_unit(m.group(2)),
            raw_string=raw_string,
            is_strict_lower=False,
        )

    # MIN_ONLY — strict >
    m = _RE_GT_STRICT.match(s)
    if m:
        return ParsedSpec(
            spec_type=SpecType.MIN_ONLY,
            min_value=float(m.group(1)),
            max_value=None,
            unit=_extract_unit(m.group(2)),
            raw_string=raw_string,
            is_strict_lower=True,
        )

    # MAX_ONLY — NMT / ≤
    m = _RE_NMT.match(s)
    if m:
        return ParsedSpec(
            spec_type=SpecType.MAX_ONLY,
            min_value=None,
            max_value=float(m.group(1)),
            unit=_extract_unit(m.group(2)),
            raw_string=raw_string,
            is_strict_upper=False,
        )

    # MAX_ONLY — strict <
    m = _RE_LT_STRICT.match(s)
    if m:
        return ParsedSpec(
            spec_type=SpecType.MAX_ONLY,
            min_value=None,
            max_value=float(m.group(1)),
            unit=_extract_unit(m.group(2)),
            raw_string=raw_string,
            is_strict_upper=True,
        )

    # MAX_ONLY — "maximum: 0.5%"
    m = _RE_MAX_ONLY_LABEL.match(s)
    if m:
        return ParsedSpec(
            spec_type=SpecType.MAX_ONLY,
            min_value=None,
            max_value=float(m.group(1)),
            unit=_extract_unit(m.group(2)),
            raw_string=raw_string,
        )

    # Fallback — QUALITATIVE
    return ParsedSpec(
        spec_type=SpecType.QUALITATIVE,
        min_value=None,
        max_value=None,
        unit=None,
        raw_string=raw_string,
    )
