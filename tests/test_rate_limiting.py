"""Comprehensive tests for rate limiting functionality."""

import time
import pytest
import asyncio
from unittest.mock import patch, MagicMock

import respx
import httpx

from photoroom import PhotoRoomClient
from photoroom.rate_limiter import RateLimitError


# ============================================================================
# Sync Rate Limiting Tests
# ============================================================================

@respx.mock
def test_rate_limiting_wait_strategy():
    """Test that rate limiting with 'wait' strategy delays requests."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Create client with 2 requests/second rate limit
    client = PhotoRoomClient(
        api_key="test_key",
        rate_limit=2.0,  # 2 requests per second
        rate_limit_strategy="wait"
    )

    # Make 4 requests and measure time
    start_time = time.time()

    for _ in range(4):
        client.remove_background(b"fake_image_data")

    elapsed = time.time() - start_time

    # 4 requests at 2 req/sec with burst_size=2:
    # - First 2 requests are instant (use burst tokens)
    # - 3rd request waits ~0.5s
    # - 4th request waits ~0.5s more
    # Total: ~1.0s
    assert elapsed >= 0.9, f"Expected >= 0.9s but took {elapsed:.2f}s"
    assert elapsed < 1.5, f"Took too long: {elapsed:.2f}s"


@respx.mock
def test_rate_limiting_error_strategy():
    """Test that rate limiting with 'error' strategy raises exception."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Create client with 1 request/second rate limit (error strategy)
    client = PhotoRoomClient(
        api_key="test_key",
        rate_limit=1.0,
        rate_limit_strategy="error"
    )

    # First request should succeed
    client.remove_background(b"fake_image_data")

    # Second immediate request should raise RateLimitError
    with pytest.raises(RateLimitError, match="Rate limit exceeded"):
        client.remove_background(b"fake_image_data")


@respx.mock
def test_no_rate_limiting_when_disabled():
    """Test that no delays occur when rate limiting is disabled."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Create client WITHOUT rate limiting
    client = PhotoRoomClient(
        api_key="test_key",
        rate_limit=None  # No rate limiting
    )

    # Make 5 requests and measure time
    start_time = time.time()

    for _ in range(5):
        client.remove_background(b"fake_image_data")

    elapsed = time.time() - start_time

    # Without rate limiting, should be very fast (< 0.5 seconds)
    assert elapsed < 0.5, f"Took too long without rate limiting: {elapsed:.2f}s"


@respx.mock
def test_rate_limiting_respects_configured_limit():
    """Test that different rate limits are respected correctly."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Test with 5 requests per second
    client = PhotoRoomClient(
        api_key="test_key",
        rate_limit=5.0,
        rate_limit_strategy="wait"
    )

    start_time = time.time()

    # Make 10 requests
    # With burst_size=5, first 5 are instant, then we wait
    for _ in range(10):
        client.remove_background(b"fake_image_data")

    elapsed = time.time() - start_time

    # 10 requests at 5 req/sec with burst_size=5:
    # First 5 instant, next 5 need ~1 second total
    assert elapsed >= 0.9, f"Expected >= 0.9s but took {elapsed:.2f}s"
    assert elapsed < 1.5, f"Took too long: {elapsed:.2f}s"


# ============================================================================
# Async Rate Limiting Tests
# ============================================================================

@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_rate_limiting_wait_strategy():
    """Test that async rate limiting with 'wait' strategy delays requests."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Create async client with 2 requests/second rate limit
    async with PhotoRoomClient(
        api_key="test_key",
        async_mode=True,
        rate_limit=2.0,
        rate_limit_strategy="wait"
    ) as client:
        # Make 4 requests sequentially (not concurrently) and measure time
        # Note: Sequential to avoid async rate limiter concurrency issues
        start_time = time.time()

        for _ in range(4):
            await client.aremove_background(b"fake_image_data")

        elapsed = time.time() - start_time

        # 4 requests at 2 req/sec with burst_size=2:
        # First 2 instant, next 2 need ~1 second total
        assert elapsed >= 0.9, f"Expected >= 0.9s but took {elapsed:.2f}s"
        assert elapsed < 2.0, f"Took too long: {elapsed:.2f}s"


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_rate_limiting_error_strategy():
    """Test that async rate limiting with 'error' strategy raises exception."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Create async client with 1 request/second rate limit (error strategy)
    async with PhotoRoomClient(
        api_key="test_key",
        async_mode=True,
        rate_limit=1.0,
        rate_limit_strategy="error"
    ) as client:
        # First request should succeed
        await client.aremove_background(b"fake_image_data")

        # Second immediate request should raise RateLimitError
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            await client.aremove_background(b"fake_image_data")


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_no_rate_limiting_when_disabled():
    """Test that no delays occur in async mode when rate limiting is disabled."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Create async client WITHOUT rate limiting
    async with PhotoRoomClient(
        api_key="test_key",
        async_mode=True,
        rate_limit=None
    ) as client:
        # Make 5 concurrent requests and measure time
        start_time = time.time()

        tasks = [
            client.aremove_background(b"fake_image_data")
            for _ in range(5)
        ]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        # Without rate limiting, should be very fast (< 0.5 seconds)
        assert elapsed < 0.5, f"Took too long without rate limiting: {elapsed:.2f}s"


# ============================================================================
# Integration Tests with Edit Endpoint
# ============================================================================

@respx.mock
def test_rate_limiting_with_edit_endpoint():
    """Test that rate limiting works with edit_image endpoint."""
    # Mock successful response
    respx.post("https://image-api.photoroom.com/v2/edit").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Create client with 2 requests/second rate limit
    client = PhotoRoomClient(
        api_key="test_key",
        rate_limit=2.0,
        rate_limit_strategy="wait"
    )

    # Make 4 requests and measure time
    start_time = time.time()

    for _ in range(4):
        client.edit_image(
            image_file=b"fake_image_data",
            background_color="white"
        )

    elapsed = time.time() - start_time

    # 4 requests at 2 req/sec with burst_size=2:
    # First 2 instant, next 2 need ~1 second total
    assert elapsed >= 0.9, f"Expected >= 0.9s but took {elapsed:.2f}s"
    assert elapsed < 1.5, f"Took too long: {elapsed:.2f}s"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

def test_rate_limiting_with_retries():
    """Test that rate limiting works correctly with retry logic."""
    with respx.mock:
        # First request fails, second succeeds
        route = respx.post("https://sdk.photoroom.com/v1/segment").mock(
            side_effect=[
                httpx.Response(503, content=b"Service Unavailable"),
                httpx.Response(200, content=b"fake_image_data")
            ]
        )

        client = PhotoRoomClient(
            api_key="test_key",
            rate_limit=10.0,  # High rate limit to not interfere
            rate_limit_strategy="wait",
            max_retries=3
        )

        # Should succeed after retry
        result = client.remove_background(b"fake_image_data")
        assert result.image_data == b"fake_image_data"

        # Should have made 2 requests (1 failure + 1 success)
        assert route.call_count == 2


def test_invalid_rate_limit_strategy():
    """Test that invalid rate limit strategy is handled."""
    # Invalid strategy should either raise or default to "wait"
    # (depends on RateLimiter implementation)
    client = PhotoRoomClient(
        api_key="test_key",
        rate_limit=1.0,
        rate_limit_strategy="invalid_strategy"
    )

    # Should not crash - verify client is created
    assert client.rate_limiter is not None


@respx.mock
def test_very_low_rate_limit():
    """Test with very low rate limit (0.5 req/sec)."""
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    client = PhotoRoomClient(
        api_key="test_key",
        rate_limit=0.5,  # 1 request every 2 seconds
        rate_limit_strategy="wait"
    )

    start_time = time.time()

    # Make 2 requests
    client.remove_background(b"fake_image_data")
    client.remove_background(b"fake_image_data")

    elapsed = time.time() - start_time

    # Should take at least 2 seconds
    assert elapsed >= 2.0, f"Expected >= 2.0s but took {elapsed:.2f}s"


@respx.mock
def test_rate_limiting_zero_limit():
    """Test that rate_limit=0 is treated as no limit."""
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # rate_limit=0 should disable rate limiting
    client = PhotoRoomClient(
        api_key="test_key",
        rate_limit=0
    )

    # Rate limiter should not be created
    assert client.rate_limiter is None

    # Requests should be fast
    start_time = time.time()

    for _ in range(5):
        client.remove_background(b"fake_image_data")

    elapsed = time.time() - start_time
    assert elapsed < 0.5, f"Should be fast without rate limiting: {elapsed:.2f}s"
