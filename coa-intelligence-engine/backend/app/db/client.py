import structlog
from supabase import create_client, AsyncClient
from app.config import get_settings

logger = structlog.get_logger(__name__)

_supabase_client: AsyncClient | None = None


async def init_supabase() -> None:
    global _supabase_client
    settings = get_settings()
    try:
        _supabase_client = create_client(
            settings.supabase_url, settings.supabase_service_key
        )
        logger.info("Supabase client initialised")
    except Exception as exc:
        logger.error("Failed to initialise Supabase client", exc_info=exc)
        raise


def get_client() -> AsyncClient:
    if _supabase_client is None:
        raise RuntimeError("Supabase client not initialised — call init_supabase() first")
    return _supabase_client
