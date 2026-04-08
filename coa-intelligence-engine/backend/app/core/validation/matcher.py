"""
Product matcher: fuzzy-match extracted product_name against the products table.
Returns (product_id, score) or (None, 0.0) if no match above threshold.
"""
from __future__ import annotations

import re
import structlog

logger = structlog.get_logger(__name__)

MATCH_THRESHOLD = 0.80


def _normalise(text: str) -> str:
    """Lowercase, strip punctuation and extra whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _token_overlap_score(a: str, b: str) -> float:
    """Jaccard similarity on word tokens."""
    tokens_a = set(_normalise(a).split())
    tokens_b = set(_normalise(b).split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def _levenshtein(a: str, b: str) -> int:
    """Pure-Python Levenshtein distance (fallback if python-Levenshtein unavailable)."""
    if len(a) < len(b):
        return _levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            ins = prev[j + 1] + 1
            dlt = curr[j] + 1
            sub = prev[j] + (0 if ca == cb else 1)
            curr.append(min(ins, dlt, sub))
        prev = curr
    return prev[len(b)]


def _levenshtein_score(a: str, b: str) -> float:
    """Normalised similarity: 1 - (distance / max_len)."""
    a_n, b_n = _normalise(a), _normalise(b)
    max_len = max(len(a_n), len(b_n))
    if max_len == 0:
        return 1.0
    try:
        from Levenshtein import distance  # type: ignore

        dist = distance(a_n, b_n)
    except ImportError:
        dist = _levenshtein(a_n, b_n)
    return 1.0 - dist / max_len


def match_product(
    extracted_name: str | None,
    products: list[dict],
) -> tuple[str | None, float]:
    """
    Match extracted product name against a list of product dicts with 'id' and 'name'.
    Returns (product_id, score).  Returns (None, 0.0) if no match ≥ MATCH_THRESHOLD.
    """
    if not extracted_name or not products:
        return None, 0.0

    best_id: str | None = None
    best_score: float = 0.0

    for product in products:
        product_name = product.get("name", "")
        token_score = _token_overlap_score(extracted_name, product_name)
        lev_score = _levenshtein_score(extracted_name, product_name)
        score = (token_score + lev_score) / 2.0

        if score > best_score:
            best_score = score
            best_id = str(product["id"])

    if best_score >= MATCH_THRESHOLD:
        logger.info(
            "Product matched",
            extracted=extracted_name,
            product_id=best_id,
            score=best_score,
        )
        return best_id, best_score

    logger.info(
        "No product match above threshold",
        extracted=extracted_name,
        best_score=best_score,
        threshold=MATCH_THRESHOLD,
    )
    return None, best_score
