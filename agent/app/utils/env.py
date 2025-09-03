from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=1)
def get_redis_url() -> Optional[str]:
    # Primary: REDIS_URL; Fallback: AGENT_REDIS_URL (for legacy/start scripts)
    url = os.getenv("REDIS_URL") or os.getenv("AGENT_REDIS_URL")
    return url or None


@lru_cache(maxsize=1)
def get_postgres_url() -> Optional[str]:
    # Prefer container-safe AGENT_DATABASE_URL; fallback to generic DATABASE_URL; finally compose from POSTGRES_* if available
    url = os.getenv("AGENT_DATABASE_URL") or os.getenv("DATABASE_URL")
    if url:
        return url
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    if all([host, port, user, password, db]):
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return None


@lru_cache(maxsize=1)
def is_tracing_enabled() -> bool:
    return os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"