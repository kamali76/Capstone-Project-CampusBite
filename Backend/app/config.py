"""Application settings, read from environment variables (or a local .env file).

Secrets (JWT secret, OpenAI key) are never hard-coded; see .env.example.
"""
import logging
import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("campusbite")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/campusbite.db"

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    cors_origins: str = "http://localhost:5173"

    # bcrypt cost factor (12 is a sensible production default; tests lower it for speed)
    bcrypt_rounds: int = 12

    # Background reminder job
    reminder_after_minutes: int = 15
    reminder_interval_seconds: int = 60
    enable_background_tasks: bool = True

    # Demo data
    seed_demo_data: bool = False
    seed_demo_password: str = ""

    # AI (part 3)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.jwt_secret:
        # Safe fallback so the app still starts; tokens just stop working on restart.
        settings.jwt_secret = secrets.token_hex(32)
        logger.warning(
            "JWT_SECRET is not set - generated a temporary one. "
            "Set JWT_SECRET in your .env so logins survive restarts."
        )
    return settings
