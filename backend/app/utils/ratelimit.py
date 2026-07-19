"""Token bucket rate limiter — used by all ingestion modules.

Each module has its own module-level bucket sized to its API's rate limit:
- GitHub REST: 5000/hr ≈ 1.39 req/s sustained
- arxiv: 1 req per 3s
- Hacker News: undocumented, ~1 req/s
- Product Hunt: 900 req / 15 min = 1 req/s sustained
"""
from __future__ import annotations

import asyncio
import time
from collections import deque


class TokenBucket:
    """Async token-bucket rate limiter.

    Args:
        capacity: max tokens the bucket can hold
        refill_per_second: tokens added per second
    """

    def __init__(self, capacity: float, refill_per_second: float) -> None:
        self.capacity = float(capacity)
        self.refill_per_second = float(refill_per_second)
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()
        self._waiters: deque[asyncio.Future] = deque()

    def _refill(self) -> None:
        now = time.monotonic()
        delta = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + delta * self.refill_per_second)
        self._last_refill = now

    async def acquire(self, tokens: float = 1.0) -> None:
        """Wait until `tokens` are available, then consume them."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                # Compute wait time
                needed = tokens - self._tokens
                wait = needed / self.refill_per_second
            await asyncio.sleep(min(wait, 0.5))
