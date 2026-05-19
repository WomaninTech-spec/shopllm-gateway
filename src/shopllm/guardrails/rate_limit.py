"""Async in-memory token-bucket rate limiter, per-key (tenant or API key)."""
from __future__ import annotations
 
import asyncio
import time
from dataclasses import dataclass, field
 
 
@dataclass(slots=True)
class Bucket:
    capacity: float
    refill_per_sec: float
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
 
    def __post_init__(self) -> None:
        self.tokens = self.capacity
        self.last_refill = time.monotonic()
 
    def _refill(self) -> None:
        now = time.monotonic()
        delta = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + delta * self.refill_per_sec)
        self.last_refill = now
 
    def try_consume(self, n: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False
 
 
class RateLimiter:
    def __init__(self, capacity: float = 30, refill_per_sec: float = 1.0) -> None:
        self._cap = capacity
        self._refill = refill_per_sec
        self._buckets: dict[str, Bucket] = {}
        self._lock = asyncio.Lock()
 
    async def allow(self, key: str, cost: float = 1.0) -> bool:
        async with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = Bucket(self._cap, self._refill)
                self._buckets[key] = bucket
            return bucket.try_consume(cost)