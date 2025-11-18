from __future__ import annotations

"""
Application configuration and environment loading.

This module centralizes access to environment variables used by the backend.
"""

from functools import lru_cache
from typing import Optional

from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseModel):
    """Typed application settings loaded from environment variables."""

    deepseek_api_key: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    deepseek_api_base: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")

    neo4j_uri: Optional[str] = os.getenv("NEO4J_URI")
    neo4j_user: Optional[str] = os.getenv("NEO4J_USER")
    neo4j_password: Optional[str] = os.getenv("NEO4J_PASSWORD")

    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()

