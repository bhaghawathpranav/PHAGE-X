from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Tuple


def _csv(name: str, default: str) -> Tuple[str, ...]:
    return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())


@dataclass(frozen=True)
class Settings:
    environment: str
    allowed_origins: Tuple[str, ...]
    log_level: str
    app_version: str
    feedback_db: str
    embedding_cache: str
    api_key: str | None
    rate_limit_per_minute: int
    audit_db: str

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    environment = os.getenv("PHAGEX_ENVIRONMENT", "development").lower()
    if environment not in {"development", "test", "production"}:
        raise RuntimeError("PHAGEX_ENVIRONMENT must be development, test, or production")
    origins = _csv(
        "PHAGEX_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    if environment == "production" and any(origin == "*" for origin in origins):
        raise RuntimeError("Wildcard CORS origins are not allowed in production")
    api_key = os.getenv("PHAGEX_API_KEY")
    if environment == "production" and (not api_key or len(api_key) < 24):
        raise RuntimeError("PHAGEX_API_KEY must contain at least 24 characters in production")
    return Settings(
        environment=environment,
        allowed_origins=origins,
        log_level=os.getenv("PHAGEX_LOG_LEVEL", "INFO").upper(),
        app_version=os.getenv("PHAGEX_VERSION", "0.2.0"),
        feedback_db=os.getenv("PHAGEX_FEEDBACK_DB", "work/phagex_feedback.sqlite3"),
        embedding_cache=os.getenv("PHAGEX_EMBEDDING_CACHE", "work/esm2_embeddings.sqlite3"),
        api_key=api_key,
        rate_limit_per_minute=int(os.getenv("PHAGEX_RATE_LIMIT_PER_MINUTE", "60")),
        audit_db=os.getenv("PHAGEX_AUDIT_DB", "work/phagex_audit.sqlite3"),
    )
