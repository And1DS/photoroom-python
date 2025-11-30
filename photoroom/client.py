"""PhotoRoom API Client.

This module provides the main PhotoRoomClient class for interacting with
the PhotoRoom REST API in both synchronous and asynchronous modes.
"""

import warnings
from typing import Any, Dict, Optional, Union
from pathlib import Path

import httpx

from .exceptions import parse_error_response
from .types import AccountInfo, ImageResponse
from .utils import get_api_key, extract_response_metadata
from .retry import RetryConfig
from .rate_limiter import RateLimiter


class PhotoRoomClient:
    """Main client for interacting with the PhotoRoom API.

    Supports both synchronous and asynchronous modes.

    Examples:
        Sync mode:
            >>> client = PhotoRoomClient(api_key="your-api-key")
            >>> result = client.remove_background("photo.jpg", bg_color="white")
            >>> result.save("output.png")

        Async mode:
            >>> async with PhotoRoomClient(async_mode=True) as client:
            ...     result = await client.remove_background("photo.jpg")
            ...     result.save("output.png")

    Attributes:
        api_key: PhotoRoom API key
        async_mode: Whether to use async HTTP client
        timeout: Request timeout in seconds
    """

    # API base URLs
    SDK_BASE_URL = "https://sdk.photoroom.com"
    IMAGE_API_BASE_URL = "https://image-api.photoroom.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        async_mode: bool = False,
        timeout: float = 120.0,
        # Retry configuration
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        retry_on_status: Optional[list] = None,
        # Rate limiting
        rate_limit: Optional[float] = None,
        rate_limit_strategy: str = "wait",
        # Image validation
        validate_images: bool = True,
        auto_resize: bool = False,
        auto_convert: bool = False,
    ):
        """Initialize PhotoRoom client.

        Args:
            api_key: PhotoRoom API key. If not provided, will look for
                PHOTOROOM_API_KEY environment variable.
            async_mode: If True, use async HTTP client. Default: False.
            timeout: Request timeout in seconds. Default: 120.0.
            max_retries: Maximum number of retry attempts for failed requests. Default: 3.
            retry_backoff: Exponential backoff multiplier for retries. Default: 2.0.
            retry_on_status: HTTP status codes to retry on. Default: [500, 502, 503, 504].
            rate_limit: Maximum requests per second. None for no limit.
            rate_limit_strategy: How to handle rate limit: "wait" (sleep) or "error" (raise).
            validate_images: Validate image format and size before upload. Default: True.
            auto_resize: Automatically resize images that exceed size/dimension limits. Default: False.
            auto_convert: Automatically convert unsupported formats (HEIC, TIFF, etc.) to WebP. Default: False.

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self.api_key = get_api_key(api_key)
        self.async_mode = async_mode
        self.timeout = timeout
        self.validate_images = validate_images
        self.auto_resize = auto_resize
        self.auto_convert = auto_convert

        # Initialize retry configuration
        self.retry_config = RetryConfig(
            max_retries=max_retries,
            backoff_factor=retry_backoff,
            retry_on_status=retry_on_status,
        )

        # Initialize rate limiter if specified
        self.rate_limiter: Optional[RateLimiter] = None
        if rate_limit is not None and rate_limit > 0:
            self.rate_limiter = RateLimiter(
                rate_limit=rate_limit,
                strategy=rate_limit_strategy,
            )

        # Initialize HTTP client
        self._client: Union[httpx.Client, httpx.AsyncClient, None] = None
        self._is_context_managed = False

        # Detect sandbox API key and emit warning
        if self.is_sandbox:
            warnings.warn(
                "Sandbox API key detected. Note: Some endpoints like get_account() "
                "may not be available with sandbox keys. Use a production API key "
                "for full access to all features.",
                UserWarning,
                stacklevel=2,
            )

        if not async_mode:
            # For sync mode, create client immediately
            self._client = self._create_sync_client()

    @property
    def is_sandbox(self) -> bool:
        """Check if using a sandbox API key.

        Sandbox API keys start with 'sandbox_' and may have limited functionality.

        Returns:
            True if using a sandbox API key, False otherwise.
        """
        return self.api_key.startswith("sandbox_")

    def _create_sync_client(self) -> httpx.Client:
        """Create synchronous HTTP client.

        Returns:
            Configured httpx.Client instance
        """
        return httpx.Client(
            headers=self._get_headers(),
            timeout=self.timeout,
        )

    def _create_async_client(self) -> httpx.AsyncClient:
        """Create asynchronous HTTP client.

        Returns:
            Configured httpx.AsyncClient instance
        """
        return httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=self.timeout,
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests.

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "X-Api-Key": self.api_key,
        }

    def _get_client(self) -> Union[httpx.Client, httpx.AsyncClient]:
        """Get HTTP client instance.

        Returns:
            HTTP client instance

        Raises:
            RuntimeError: If async client is accessed outside context manager
        """
        if self._client is None:
            if self.async_mode:
                raise RuntimeError(
                    "Async client must be used as context manager: "
                    "async with PhotoRoomClient(async_mode=True) as client: ..."
                )
            else:
                self._client = self._create_sync_client()

        return self._client

    def close(self) -> None:
        """Close the HTTP client (sync mode only).

        For async mode, use async context manager instead.
        """
        if self._client is not None and isinstance(self._client, httpx.Client):
            self._client.close()
            self._client = None

    async def aclose(self) -> None:
        """Close the async HTTP client.

        Only call this if using async mode.
        """
        if self._client is not None and isinstance(self._client, httpx.AsyncClient):
            await self._client.aclose()
            self._client = None

    def __enter__(self) -> "PhotoRoomClient":
        """Enter sync context manager.

        Returns:
            Self

        Raises:
            ValueError: If used with async_mode=True
        """
        if self.async_mode:
            raise ValueError(
                "Cannot use sync context manager with async_mode=True. "
                "Use 'async with' instead."
            )
        self._is_context_managed = True
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit sync context manager."""
        self.close()
        self._is_context_managed = False

    async def __aenter__(self) -> "PhotoRoomClient":
        """Enter async context manager.

        Returns:
            Self

        Raises:
            ValueError: If used with async_mode=False
        """
        if not self.async_mode:
            raise ValueError(
                "Cannot use async context manager with async_mode=False. "
                "Use 'with' instead or set async_mode=True."
            )
        self._client = self._create_async_client()
        self._is_context_managed = True
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.aclose()
        self._is_context_managed = False

    def _make_request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with retry logic (sync).

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            HTTPError: If request fails after all retries
        """
        client = self._get_client()
        last_exception = None

        # Apply rate limiting if configured
        if self.rate_limiter:
            self.rate_limiter.acquire()

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Make the request
                response = client.request(method, url, **kwargs)

                # Only raise for status if it's a retryable error code
                # Otherwise let _handle_response parse the error
                if response.status_code >= 400:
                    if self.retry_config.should_retry(response.status_code, attempt):
                        response.raise_for_status()
                    else:
                        # Non-retryable error, return to let _handle_response deal with it
                        return response

                return response

            except httpx.HTTPStatusError as e:
                last_exception = e

                # Calculate and apply backoff
                if attempt < self.retry_config.max_retries:
                    import time
                    backoff = self.retry_config.calculate_backoff(attempt)
                    time.sleep(backoff)
                else:
                    # Last attempt failed, raise the error
                    raise

            except httpx.RequestError as e:
                # Network errors - retry
                last_exception = e

                if attempt < self.retry_config.max_retries:
                    import time
                    backoff = self.retry_config.calculate_backoff(attempt)
                    time.sleep(backoff)
                else:
                    raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise RuntimeError("Request failed after all retry attempts")

    async def _make_request_with_retry_async(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with retry logic (async).

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            HTTPError: If request fails after all retries
        """
        import asyncio
        client = self._get_client()
        last_exception = None

        # Apply rate limiting if configured
        if self.rate_limiter:
            await self.rate_limiter.aacquire()

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Make the request
                response = await client.request(method, url, **kwargs)

                # Only raise for status if it's a retryable error code
                # Otherwise let _handle_response parse the error
                if response.status_code >= 400:
                    if self.retry_config.should_retry(response.status_code, attempt):
                        response.raise_for_status()
                    else:
                        # Non-retryable error, return to let _handle_response deal with it
                        return response

                return response

            except httpx.HTTPStatusError as e:
                last_exception = e

                # Calculate and apply backoff
                if attempt < self.retry_config.max_retries:
                    backoff = self.retry_config.calculate_backoff(attempt)
                    await asyncio.sleep(backoff)
                else:
                    # Last attempt failed, raise the error
                    raise

            except httpx.RequestError as e:
                # Network errors - retry
                last_exception = e

                if attempt < self.retry_config.max_retries:
                    backoff = self.retry_config.calculate_backoff(attempt)
                    await asyncio.sleep(backoff)
                else:
                    raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise RuntimeError("Request failed after all retry attempts")

    def _handle_response(
        self, response: httpx.Response, expect_json: bool = False
    ) -> Union[ImageResponse, Dict[str, Any]]:
        """Handle API response, checking for errors.

        Args:
            response: HTTP response from API
            expect_json: If True, expect JSON response. Default: False.

        Returns:
            ImageResponse for binary responses, dict for JSON responses

        Raises:
            PhotoRoomError: If API returns an error
        """
        # Check for error status codes
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except Exception:
                error_data = {"detail": response.text}

            raise parse_error_response(response.status_code, error_data)

        # Extract metadata from headers
        metadata = extract_response_metadata(response)

        # Return appropriate response type
        if expect_json:
            return response.json()
        else:
            return ImageResponse(
                image_data=response.content,
                metadata=metadata,
            )

    # Import endpoint methods
    from .endpoints.edit import edit_image, aedit_image
    from .endpoints.remove_bg import remove_background, aremove_background
    from .endpoints.account import get_account, aget_account
    from .endpoints.batch_operations import (
        batch_remove_background,
        batch_edit_image,
        _process_batch_sync,
        abatch_remove_background,
        abatch_edit_image,
        _process_batch_async,
    )

    def __del__(self) -> None:
        """Cleanup on deletion."""
        # Only close if not context managed (context manager handles its own cleanup)
        try:
            if (
                hasattr(self, "_is_context_managed")
                and not self._is_context_managed
                and hasattr(self, "_client")
                and self._client is not None
            ):
                if isinstance(self._client, httpx.Client):
                    try:
                        self._client.close()
                    except Exception:
                        pass
        except Exception:
            # Silently ignore any errors during cleanup
            pass
