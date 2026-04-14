import asyncio
import time
from collections import deque

from config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW


class RateLimiter:
    """Sliding-window rate limiter for TWSE API calls."""

    def __init__(self, max_requests: int = RATE_LIMIT_REQUESTS, window: float = RATE_LIMIT_WINDOW):
        self._max = max_requests
        self._window = window
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            # Remove timestamps outside the window
            while self._timestamps and now - self._timestamps[0] >= self._window:
                self._timestamps.popleft()
            if len(self._timestamps) >= self._max:
                sleep_time = self._window - (now - self._timestamps[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                self._timestamps.popleft()
            self._timestamps.append(time.monotonic())


twse_rate_limiter = RateLimiter()
