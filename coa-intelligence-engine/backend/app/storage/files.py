"""
Supabase Storage upload and retrieval for CoA files.
"""
from __future__ import annotations

import mimetypes
import structlog
from pathlib import Path

from app.db.client import get_client
from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


async def upload_coa_file(
    file_bytes: bytes,
    filename: str,
    submission_id: str,
) -> str:
    """Upload raw CoA file to Supabase Storage and return the storage path."""
    client = get_client()
    ext = Path(filename).suffix.lower()
    storage_path = f"{submission_id}/{filename}"
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    try:
        client.storage.from_(settings.coa_storage_bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": mime_type, "upsert": "true"},
        )
        logger.info("CoA file uploaded", path=storage_path, size=len(file_bytes))
        return storage_path
    except Exception as exc:
        logger.error("Failed to upload CoA file", path=storage_path, exc_info=exc)
        raise


async def download_coa_file(storage_path: str) -> bytes:
    """Download raw CoA file from Supabase Storage."""
    client = get_client()
    try:
        data = client.storage.from_(settings.coa_storage_bucket).download(storage_path)
        logger.info("CoA file downloaded", path=storage_path, size=len(data))
        return data
    except Exception as exc:
        logger.error("Failed to download CoA file", path=storage_path, exc_info=exc)
        raise


def get_public_url(storage_path: str) -> str:
    """Return a signed URL for the file (for audit trail display)."""
    client = get_client()
    result = client.storage.from_(settings.coa_storage_bucket).create_signed_url(
        storage_path, expires_in=3600
    )
    return result.get("signedURL", "")
