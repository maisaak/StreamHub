from __future__ import annotations

import time
from typing import Any

import structlog

from app.config import settings

log = structlog.get_logger()

try:
    from redis import asyncio as aioredis

    _has_redis = True
except ImportError:  # pragma: no cover
    _has_redis = False
    aioredis = None  # type: ignore


class FakeRedis:
    """In-memory fallback so API works without Redis (dev/tests)."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str) -> Any:
        item = self._data.get(key)
        if not item:
            return None
        val, exp = item
        if exp and time.time() > exp:
            self._data.pop(key, None)
            return None
        return val

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        self._data[key] = (value, time.time() + ex if ex else None)
        return True

    async def delete(self, *keys: str) -> int:
        n = 0
        for k in keys:
            if self._data.pop(k, None) is not None:
                n += 1
        return n

    async def incr(self, key: str) -> int:
        raw = await self.get(key)
        val = (int(raw) if raw else 0) + 1
        exp = self._data.get(key, (None, None))[1]
        self._data[key] = (str(val), exp)
        return val

    async def expire(self, key: str, seconds: int) -> bool:
        if key in self._data:
            val, _ = self._data[key]
            self._data[key] = (val, time.time() + seconds)
            return True
        return False

    async def ping(self) -> bool:
        return True


_client: Any = None


async def get_redis() -> Any:
    global _client
    if _client is not None:
        return _client
    if _has_redis:
        try:
            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await client.ping()
            _client = client
            return _client
        except Exception as e:
            log.warning("redis_unavailable_fallback", error=str(e))
    _client = FakeRedis()
    return _client


def reset_redis_client() -> None:
    global _client
    _client = None
