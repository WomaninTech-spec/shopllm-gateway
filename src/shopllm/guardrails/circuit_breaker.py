"""Simple async circuit breaker per provider."""
from __future__ import annotations
 
import asyncio
import time
from enum import Enum
 
 
class State(str, Enum):
    CLOSED = "closed"     # all good
    OPEN = "open"         # blocking calls
    HALF_OPEN = "half_open"
 
 
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_seconds: float = 30.0) -> None:
        self._failures = 0
        self._state = State.CLOSED
        self._opened_at = 0.0
        self._threshold = failure_threshold
        self._recovery = recovery_seconds
        self._lock = asyncio.Lock()
 
    @property
    def state(self) -> State:
        return self._state
 
    async def before_call(self) -> None:
        async with self._lock:
            if self._state is State.OPEN:
                if time.monotonic() - self._opened_at >= self._recovery:
                    self._state = State.HALF_OPEN
                else:
                    raise RuntimeError("Circuit breaker is OPEN — provider unhealthy.")
 
    async def on_success(self) -> None:
        async with self._lock:
            self._failures = 0
            self._state = State.CLOSED
 
    async def on_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            if self._failures >= self._threshold:
                self._state = State.OPEN
                self._opened_at = time.monotonic()