"""Retry logic with exponential backoff for PhotoRoom API.

This module provides retry functionality for handling transient errors
when communicating with the PhotoRoom API.
"""

import time
import random
from typing import Callable, List, Optional, TypeVar, Any
from functools import wraps

import httpx

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff (default: 2.0)
        retry_on_status: List of HTTP status codes to retry on
        max_backoff: Maximum backoff time in seconds
        jitter: Add random jitter to backoff to avoid thundering herd
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        retry_on_status: Optional[List[int]] = None,
        max_backoff: float = 60.0,
        jitter: bool = True,
    ):
        """Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            backoff_factor: Exponential backoff multiplier (default: 2.0)
            retry_on_status: HTTP status codes to retry on (default: [500, 502, 503, 504])
            max_backoff: Maximum backoff time in seconds (default: 60.0)
            jitter: Add random jitter to backoff (default: True)
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_on_status = retry_on_status or [500, 502, 503, 504]
        self.max_backoff = max_backoff
        self.jitter = jitter

    def calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff time for given attempt number.

        Uses exponential backoff with optional jitter:
        backoff = min(backoff_factor^attempt, max_backoff)

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Backoff time in seconds
        """
        # Calculate exponential backoff
        backoff = min(
            self.backoff_factor ** attempt,
            self.max_backoff
        )

        # Add jitter if enabled (±25% random variation)
        if self.jitter and backoff > 0:
            jitter_range = backoff * 0.25
            backoff += random.uniform(-jitter_range, jitter_range)
            backoff = max(0, backoff)  # Ensure non-negative

        return backoff

    def should_retry(self, status_code: int, attempt: int) -> bool:
        """Determine if request should be retried.

        Args:
            status_code: HTTP status code from response
            attempt: Current attempt number (0-indexed)

        Returns:
            True if should retry, False otherwise
        """
        return (
            attempt < self.max_retries
            and status_code in self.retry_on_status
        )


def retry_on_error(config: RetryConfig):
    """Decorator to add retry logic to a function.

    Args:
        config: RetryConfig instance with retry settings

    Returns:
        Decorated function with retry logic

    Example:
        >>> retry_config = RetryConfig(max_retries=3, backoff_factor=2.0)
        >>> @retry_on_error(retry_config)
        ... def make_api_call():
        ...     # API call that might fail
        ...     pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    last_exception = e

                    # Check if we should retry
                    if not config.should_retry(e.response.status_code, attempt):
                        raise

                    # Calculate and apply backoff
                    if attempt < config.max_retries:
                        backoff = config.calculate_backoff(attempt)
                        time.sleep(backoff)

                except httpx.RequestError as e:
                    # Network errors - retry regardless of status code
                    last_exception = e

                    if attempt < config.max_retries:
                        backoff = config.calculate_backoff(attempt)
                        time.sleep(backoff)
                    else:
                        raise

            # If we get here, all retries failed
            if last_exception:
                raise last_exception
            raise RuntimeError("All retry attempts failed")

        return wrapper
    return decorator


async def async_retry_on_error(config: RetryConfig):
    """Async decorator to add retry logic to an async function.

    Args:
        config: RetryConfig instance with retry settings

    Returns:
        Decorated async function with retry logic

    Example:
        >>> retry_config = RetryConfig(max_retries=3)
        >>> @async_retry_on_error(retry_config)
        ... async def make_api_call():
        ...     # Async API call that might fail
        ...     pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            import asyncio
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    last_exception = e

                    # Check if we should retry
                    if not config.should_retry(e.response.status_code, attempt):
                        raise

                    # Calculate and apply backoff
                    if attempt < config.max_retries:
                        backoff = config.calculate_backoff(attempt)
                        await asyncio.sleep(backoff)

                except httpx.RequestError as e:
                    # Network errors - retry regardless of status code
                    last_exception = e

                    if attempt < config.max_retries:
                        backoff = config.calculate_backoff(attempt)
                        await asyncio.sleep(backoff)
                    else:
                        raise

            # If we get here, all retries failed
            if last_exception:
                raise last_exception
            raise RuntimeError("All retry attempts failed")

        return wrapper
    return decorator
