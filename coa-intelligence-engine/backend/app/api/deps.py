"""Shared FastAPI dependencies."""
from app.config import Settings, get_settings
from fastapi import Depends


def settings_dep() -> Settings:
    return get_settings()
