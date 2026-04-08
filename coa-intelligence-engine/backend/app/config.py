from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Keys
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude Vision")
    gemini_api_key: str = Field(..., description="Google Gemini API key for fallback extraction")

    # Supabase
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_service_key: str = Field(..., description="Supabase service role key")

    # App config
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    max_file_size_mb: int = Field(default=50)
    extraction_confidence_threshold: float = Field(default=0.6)
    extraction_warning_band_percent: float = Field(default=5.0)

    # CORS
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"]
    )

    # Claude model
    claude_model: str = Field(default="claude-opus-4-6")
    gemini_model: str = Field(default="gemini-1.5-flash")

    # Storage bucket
    coa_storage_bucket: str = Field(default="coa-uploads")


@lru_cache
def get_settings() -> Settings:
    return Settings()
