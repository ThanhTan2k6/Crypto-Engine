"""
Unit Tests for Redis & In-Memory LLMOps Cache Manager.
Verifies caching lifecycle, payload hash determinism, and TTL expiry.
"""

import asyncio

import pytest

from src.llmops.cache import AuditCacheManager


@pytest.mark.asyncio
async def test_cache_set_get_and_stats():
    """Verify basic set, get, and hit/miss statistics in cache."""
    cache = AuditCacheManager(default_ttl_seconds=60, enable_in_memory_fallback=True)

    # Miss check
    res = await cache.get("test", "nonexistent")
    assert res is None
    stats = cache.get_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0

    # Set data
    payload = {"symbol": "BTCUSDT", "verdict": "PROCEED_WITH_CAUTION", "fomo_index": 35.0}
    success = await cache.set("test", "btc_audit", payload, ttl_seconds=60)
    assert success is True

    # Hit check
    cached = await cache.get("test", "btc_audit")
    assert cached is not None
    assert cached["symbol"] == "BTCUSDT"
    assert cached["fomo_index"] == 35.0

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["hit_ratio_pct"] == 50.0  # 1 hit, 1 miss


@pytest.mark.asyncio
async def test_cache_payload_hash_partitioning():
    """Verify deterministic hash generation partitions cache entries by input."""
    cache = AuditCacheManager(default_ttl_seconds=60, enable_in_memory_fallback=True)

    hash_a = cache.compute_payload_hash({"price": 95000.0, "mvrv": 2.1})
    hash_b = cache.compute_payload_hash({"price": 95000.0, "mvrv": 4.5})

    assert hash_a != hash_b
    assert len(hash_a) == 16

    await cache.set("audit", "BTC", {"verdict": "CAUTION"}, payload_hash=hash_a)
    await cache.set("audit", "BTC", {"verdict": "REJECT"}, payload_hash=hash_b)

    res_a = await cache.get("audit", "BTC", payload_hash=hash_a)
    res_b = await cache.get("audit", "BTC", payload_hash=hash_b)

    assert res_a is not None and res_a["verdict"] == "CAUTION"
    assert res_b is not None and res_b["verdict"] == "REJECT"


@pytest.mark.asyncio
async def test_cache_ttl_expiry():
    """Verify in-memory fallback respects TTL expiration."""
    cache = AuditCacheManager(default_ttl_seconds=1, enable_in_memory_fallback=True)

    await cache.set("short_lived", "key1", {"status": "fresh"}, ttl_seconds=1)

    # Immediately available
    res = await cache.get("short_lived", "key1")
    assert res is not None

    # Wait for expiry
    await asyncio.sleep(1.1)
    res_after = await cache.get("short_lived", "key1")
    assert res_after is None
