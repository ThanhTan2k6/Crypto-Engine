"""
Redis & In-Memory Caching Architecture for CryptoIntel-Engine.
Provides fast snapshot caching for deterministic market data and AI audit memos.
Reduces duplicate LLM invocations and guarantees graceful degradation when Redis is offline.
"""

import hashlib
import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# Try importing redis; fallback to None if not installed
try:
    import redis.asyncio as aioredis

    REDIS_ASYNC_MODULE: Any = aioredis
except ImportError:
    REDIS_ASYNC_MODULE = None


class AuditCacheManager:
    """
    Unified caching manager with Redis backend and automatic In-Memory LRU fallback.
    Thread-safe and async-compatible.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        default_ttl_seconds: int = 300,
        enable_in_memory_fallback: bool = True,
    ) -> None:
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.default_ttl = default_ttl_seconds
        self.enable_fallback = enable_in_memory_fallback

        self._redis_client: Any = None
        self._redis_available: bool = False
        self._in_memory_cache: dict[str, tuple[float, str]] = {}  # key -> (expiry_timestamp, json_str)
        self._hits: int = 0
        self._misses: int = 0

    async def initialize(self) -> None:
        """Initialize Redis connection if available."""
        if REDIS_ASYNC_MODULE is not None:
            try:
                self._redis_client = REDIS_ASYNC_MODULE.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                )
                await self._redis_client.ping()
                self._redis_available = True
                logger.info("Connected to Redis at %s", self.redis_url)
            except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                logger.warning(
                    "Redis connection failed (%s); operating with in-memory cache fallback.",
                    e,
                )
                self._redis_available = False
        else:
            logger.info("aioredis not installed; using in-memory cache.")
            self._redis_available = False

    def is_redis_connected(self) -> bool:
        """Return whether Redis client is live and reachable."""
        return self._redis_available

    def _generate_cache_key(self, namespace: str, key: str, payload_hash: str | None = None) -> str:
        clean_ns = namespace.strip(":")
        clean_key = key.strip(":")
        if payload_hash:
            return f"cryptointel:{clean_ns}:{clean_key}:{payload_hash}"
        return f"cryptointel:{clean_ns}:{clean_key}"

    @staticmethod
    def compute_payload_hash(payload: dict[str, Any] | None) -> str:
        """Compute deterministic SHA256 signature for request payloads."""
        if not payload:
            return "empty"
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    async def get(
        self, namespace: str, key: str, payload_hash: str | None = None
    ) -> dict[str, Any] | None:
        """Retrieve cached JSON payload from Redis or in-memory fallback."""
        cache_key = self._generate_cache_key(namespace, key, payload_hash)

        # 1. Try Redis if live
        if self._redis_available and self._redis_client is not None:
            try:
                cached_data = await self._redis_client.get(cache_key)
                if cached_data is not None:
                    self._hits += 1
                    return json.loads(cached_data)  # type: ignore[no-any-return]
            except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                logger.warning("Redis GET failed for %s: %s; checking in-memory fallback.", cache_key, e)
                self._redis_available = False

        # 2. Check in-memory fallback
        if self.enable_fallback and cache_key in self._in_memory_cache:
            expiry, json_str = self._in_memory_cache[cache_key]
            if time.time() < expiry:
                self._hits += 1
                return json.loads(json_str)  # type: ignore[no-any-return]
            else:
                # Expired
                del self._in_memory_cache[cache_key]

        self._misses += 1
        return None

    async def set(
        self,
        namespace: str,
        key: str,
        data: dict[str, Any],
        ttl_seconds: int | None = None,
        payload_hash: str | None = None,
    ) -> bool:
        """Store JSON payload in Redis and in-memory cache."""
        cache_key = self._generate_cache_key(namespace, key, payload_hash)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        serialized = json.dumps(data, default=str)

        success = False

        # 1. Store in Redis
        if self._redis_available and self._redis_client is not None:
            try:
                await self._redis_client.set(cache_key, serialized, ex=ttl)
                success = True
            except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                logger.warning("Redis SET failed for %s: %s; falling back to in-memory.", cache_key, e)
                self._redis_available = False

        # 2. Store in In-memory fallback
        if self.enable_fallback:
            self._in_memory_cache[cache_key] = (time.time() + ttl, serialized)
            success = True

        return success

    async def delete(self, namespace: str, key: str, payload_hash: str | None = None) -> bool:
        """Evict a specific key from cache."""
        cache_key = self._generate_cache_key(namespace, key, payload_hash)
        if self._redis_available and self._redis_client is not None:
            try:
                await self._redis_client.delete(cache_key)
            except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                logger.warning("Redis DELETE failed for %s: %s", cache_key, e)

        if cache_key in self._in_memory_cache:
            del self._in_memory_cache[cache_key]
        return True

    def get_stats(self) -> dict[str, Any]:
        """Return cache health and hit/miss statistics."""
        total_requests = self._hits + self._misses
        hit_ratio = (self._hits / total_requests) if total_requests > 0 else 0.0
        return {
            "redis_connected": self._redis_available,
            "in_memory_entries": len(self._in_memory_cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio_pct": round(hit_ratio * 100.0, 2),
        }

    async def clear_all(self) -> None:
        """Purge in-memory cache and local keys."""
        self._in_memory_cache.clear()
        if self._redis_available and self._redis_client is not None:
            try:
                keys = await self._redis_client.keys("cryptointel:*")
                if keys:
                    await self._redis_client.delete(*keys)
            except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                logger.warning("Failed to flush Redis keys: %s", e)


# Global singleton instance
audit_cache = AuditCacheManager()
