"""
JWT token blacklist with optional Redis backing.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Optional

try:
    import redis
except Exception:  # pragma: no cover - optional dependency at runtime
    redis = None

_blacklist_instance = None
_instance_lock = threading.Lock()


class InMemoryTokenBlacklist:
    """Simple in-memory blacklist with TTL tracking."""

    def __init__(self) -> None:
        self._tokens: dict[str, float] = {}
        self._lock = threading.Lock()

    def add_token(self, jti: str, expires_in: int) -> None:
        if not jti or expires_in <= 0:
            return
        expires_at = time.time() + expires_in
        with self._lock:
            self._tokens[jti] = expires_at

    def is_blacklisted(self, jti: str) -> bool:
        if not jti:
            return False
        now = time.time()
        with self._lock:
            expires_at = self._tokens.get(jti)
            if expires_at is None:
                return False
            if expires_at <= now:
                self._tokens.pop(jti, None)
                return False
            return True


class RedisTokenBlacklist:
    """Redis-backed token blacklist with TTL."""

    def __init__(self, redis_url: str) -> None:
        if redis is None:
            raise RuntimeError("redis package is not available")
        self._client = redis.Redis.from_url(redis_url)

    def ping(self) -> None:
        self._client.ping()

    def add_token(self, jti: str, expires_in: int) -> None:
        if not jti or expires_in <= 0:
            return
        self._client.setex(self._key(jti), expires_in, "1")

    def is_blacklisted(self, jti: str) -> bool:
        if not jti:
            return False
        return self._client.exists(self._key(jti)) == 1

    @staticmethod
    def _key(jti: str) -> str:
        return f"token_blacklist:{jti}"


def _build_blacklist(redis_url: Optional[str]):
    if redis_url:
        try:
            blacklist = RedisTokenBlacklist(redis_url)
            blacklist.ping()
            return blacklist
        except Exception:
            pass
    return InMemoryTokenBlacklist()


def get_blacklist():
    """Return a singleton blacklist instance with Redis fallback."""
    global _blacklist_instance
    if _blacklist_instance is None:
        with _instance_lock:
            if _blacklist_instance is None:
                _blacklist_instance = _build_blacklist(os.getenv("REDIS_URL"))
    return _blacklist_instance
