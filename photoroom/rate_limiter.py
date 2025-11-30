"""Rate limiting for PhotoRoom API requests.

This module provides rate limiting functionality using the token bucket algorithm
to prevent exceeding API rate limits.
"""

import time
import asyncio
from threading import Lock
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for API requests.

    Implements the token bucket algorithm to limit request rate.

    Attributes:
        rate_limit: Maximum requests per second
        burst_size: Maximum burst size (tokens in bucket)
        tokens: Current number of available tokens
        last_update: Timestamp of last token update
    """

    def __init__(
        self,
        rate_limit: float,
        burst_size: Optional[int] = None,
        strategy: str = "wait",
    ):
        """Initialize rate limiter.

        Args:
            rate_limit: Maximum requests per second (e.g., 10.0 for 10 req/s)
            burst_size: Maximum burst size (default: same as rate_limit)
            strategy: How to handle rate limit: "wait" (sleep) or "error" (raise exception)

        Example:
            >>> limiter = RateLimiter(rate_limit=10.0)  # 10 requests per second
            >>> limiter.acquire()  # Blocks until token is available
        """
        self.rate_limit = rate_limit
        self.burst_size = burst_size or int(rate_limit)
        self.strategy = strategy

        self.tokens = float(self.burst_size)
        self.last_update = time.monotonic()
        self._lock = Lock()

    def _refill_tokens(self) -> None:
        """Refill tokens based on time elapsed since last update."""
        now = time.monotonic()
        elapsed = now - self.last_update

        # Calculate tokens to add based on elapsed time
        tokens_to_add = elapsed * self.rate_limit

        # Update tokens (cap at burst_size)
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_update = now

    def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens from the bucket (blocking).

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Raises:
            RateLimitError: If strategy is "error" and rate limit is exceeded
        """
        with self._lock:
            self._refill_tokens()

            if self.tokens >= tokens:
                # Tokens available, consume them
                self.tokens -= tokens
                return

            if self.strategy == "error":
                raise RateLimitError(
                    f"Rate limit exceeded ({self.rate_limit} req/s). "
                    f"Available tokens: {self.tokens:.2f}"
                )

            # Calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.rate_limit

        # Release lock during sleep to allow other threads
        time.sleep(wait_time)

        # Re-acquire tokens after waiting
        with self._lock:
            self._refill_tokens()
            self.tokens -= tokens

    async def aacquire(self, tokens: int = 1) -> None:
        """Acquire tokens from the bucket (async, non-blocking).

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Raises:
            RateLimitError: If strategy is "error" and rate limit is exceeded
        """
        # Note: For async, we use a simpler approach without threading lock
        self._refill_tokens()

        if self.tokens >= tokens:
            # Tokens available, consume them
            self.tokens -= tokens
            return

        if self.strategy == "error":
            raise RateLimitError(
                f"Rate limit exceeded ({self.rate_limit} req/s). "
                f"Available tokens: {self.tokens:.2f}"
            )

        # Calculate wait time
        tokens_needed = tokens - self.tokens
        wait_time = tokens_needed / self.rate_limit

        # Wait asynchronously
        await asyncio.sleep(wait_time)

        # Re-acquire tokens after waiting
        self._refill_tokens()
        self.tokens -= tokens

    def get_available_tokens(self) -> float:
        """Get current number of available tokens.

        Returns:
            Number of available tokens
        """
        with self._lock:
            self._refill_tokens()
            return self.tokens

    def reset(self) -> None:
        """Reset the rate limiter to initial state."""
        with self._lock:
            self.tokens = float(self.burst_size)
            self.last_update = time.monotonic()

    def __repr__(self) -> str:
        """String representation of rate limiter."""
        return (
            f"RateLimiter(rate_limit={self.rate_limit} req/s, "
            f"burst_size={self.burst_size}, "
            f"available={self.tokens:.2f})"
        )


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded and strategy is 'error'."""

    pass
