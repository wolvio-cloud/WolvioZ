"""
Intake layer: Accept PDF/JPG/PNG bytes and normalise every page to PNG at 200 DPI.
Returns a list of (page_index, png_bytes) tuples.
"""
from __future__ import annotations

import io
import structlog
from pathlib import Path
from PIL import Image

logger = structlog.get_logger(__name__)

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/tiff",
    "image/webp",
}

TARGET_DPI = 200


def detect_mime_type(filename: str, file_bytes: bytes) -> str:
    """Detect MIME type from file header bytes and extension."""
    ext = Path(filename).suffix.lower()
    header = file_bytes[:8]

    if header[:4] == b"%PDF":
        return "application/pdf"
    if header[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if header[:4] in (b"II*\x00", b"MM\x00*"):
        return "image/tiff"

    ext_map = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".webp": "image/webp",
    }
    return ext_map.get(ext, "application/octet-stream")


def is_supported(mime_type: str) -> bool:
    return mime_type in SUPPORTED_MIME_TYPES


async def render_to_pages(file_bytes: bytes, mime_type: str) -> list[tuple[int, bytes]]:
    """
    Convert file bytes to a list of (page_index, png_bytes) at TARGET_DPI.

    For PDFs: each page becomes one PNG.
    For images: single page at index 0.
    """
    if mime_type == "application/pdf":
        return await _render_pdf(file_bytes)
    else:
        return await _render_image(file_bytes)


async def _render_pdf(pdf_bytes: bytes) -> list[tuple[int, bytes]]:
    """Render PDF pages to PNG using PyMuPDF (fitz) at 200 DPI."""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError("PyMuPDF not installed — pip install PyMuPDF") from exc

    pages: list[tuple[int, bytes]] = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        zoom = TARGET_DPI / 72.0  # PDF native DPI is 72
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in range(len(doc)):
            page = doc[page_num]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            png_bytes = pixmap.tobytes("png")
            pages.append((page_num, png_bytes))
            logger.debug("Rendered PDF page", page=page_num, size=len(png_bytes))

        doc.close()
        logger.info("PDF rendered to pages", total_pages=len(pages), dpi=TARGET_DPI)
        return pages

    except Exception as exc:
        logger.error("Failed to render PDF", exc_info=exc)
        raise


async def _render_image(image_bytes: bytes) -> list[tuple[int, bytes]]:
    """Normalise a single image to PNG at 200 DPI."""
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed (handles RGBA, palette modes)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Ensure DPI metadata
        current_dpi = img.info.get("dpi", (72, 72))
        if current_dpi[0] != TARGET_DPI:
            scale = TARGET_DPI / current_dpi[0]
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)

        output = io.BytesIO()
        img.save(output, format="PNG", dpi=(TARGET_DPI, TARGET_DPI))
        png_bytes = output.getvalue()

        logger.info("Image normalised to PNG", dpi=TARGET_DPI, size=len(png_bytes))
        return [(0, png_bytes)]

    except Exception as exc:
        logger.error("Failed to render image", exc_info=exc)
        raise
