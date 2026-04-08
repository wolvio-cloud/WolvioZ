"""
Claude Vision primary extraction with Gemini 1.5 Flash fallback.
Confidence threshold for fallback: < 0.6 (header) or average parameter confidence.
"""
from __future__ import annotations

import base64
import json
import re
import structlog

from app.config import get_settings
from app.core.extraction.schemas import ExtractionResult, ExtractedHeader, ExtractedParameter
from app.core.extraction.prompts import SYSTEM_PROMPT, build_user_prompt

logger = structlog.get_logger(__name__)
settings = get_settings()


def _encode_png(png_bytes: bytes) -> str:
    return base64.standard_b64encode(png_bytes).decode("utf-8")


def _clean_json_response(raw: str) -> str:
    """Strip markdown code fences if the model wraps its response."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _parse_extraction_json(raw_json: str, page_index: int, model_used: str) -> ExtractionResult:
    data = json.loads(raw_json)
    header = ExtractedHeader(**data.get("header", {}))
    parameters = [ExtractedParameter(**p) for p in data.get("parameters", [])]
    return ExtractionResult(
        header=header,
        parameters=parameters,
        extraction_notes=data.get("extraction_notes"),
        page_index=page_index,
        model_used=model_used,
    )


async def extract_with_claude(
    png_bytes: bytes, page_index: int, total_pages: int
) -> ExtractionResult:
    """Send PNG to Claude Vision and parse structured CoA data."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        encoded = _encode_png(png_bytes)
        user_prompt = build_user_prompt(page_index, total_pages)

        message = client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": encoded,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                }
            ],
        )

        raw_text = message.content[0].text
        cleaned = _clean_json_response(raw_text)
        result = _parse_extraction_json(cleaned, page_index, "claude")
        logger.info(
            "Claude extraction complete",
            page=page_index,
            params=len(result.parameters),
            header_confidence=result.header.confidence,
        )
        return result

    except Exception as exc:
        logger.error("Claude extraction failed", page=page_index, exc_info=exc)
        raise


async def extract_with_gemini(
    png_bytes: bytes, page_index: int, total_pages: int
) -> ExtractionResult:
    """Fallback: send PNG to Gemini 1.5 Flash."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=SYSTEM_PROMPT,
        )

        import PIL.Image
        import io

        img = PIL.Image.open(io.BytesIO(png_bytes))
        user_prompt = build_user_prompt(page_index, total_pages)

        response = model.generate_content([img, user_prompt])
        raw_text = response.text
        cleaned = _clean_json_response(raw_text)
        result = _parse_extraction_json(cleaned, page_index, "gemini")
        logger.info(
            "Gemini extraction complete",
            page=page_index,
            params=len(result.parameters),
            header_confidence=result.header.confidence,
        )
        return result

    except Exception as exc:
        logger.error("Gemini extraction failed", page=page_index, exc_info=exc)
        raise


async def extract_page(
    png_bytes: bytes, page_index: int, total_pages: int
) -> ExtractionResult:
    """
    Try Claude first. If average confidence < threshold, retry with Gemini.
    """
    threshold = settings.extraction_confidence_threshold

    try:
        result = await extract_with_claude(png_bytes, page_index, total_pages)
    except Exception:
        logger.warning("Claude failed — falling back to Gemini", page=page_index)
        return await extract_with_gemini(png_bytes, page_index, total_pages)

    # Check overall confidence
    avg_confidence = (
        sum(p.confidence for p in result.parameters) / len(result.parameters)
        if result.parameters
        else result.header.confidence
    )

    if avg_confidence < threshold:
        logger.info(
            "Low confidence on Claude result — trying Gemini fallback",
            page=page_index,
            avg_confidence=avg_confidence,
            threshold=threshold,
        )
        try:
            gemini_result = await extract_with_gemini(png_bytes, page_index, total_pages)
            gemini_avg = (
                sum(p.confidence for p in gemini_result.parameters) / len(gemini_result.parameters)
                if gemini_result.parameters
                else gemini_result.header.confidence
            )
            if gemini_avg > avg_confidence:
                return gemini_result
        except Exception:
            logger.warning("Gemini fallback also failed — using Claude result", page=page_index)

    return result
