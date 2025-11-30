"""PhotoRoom Python SDK.

A modern Python SDK for the PhotoRoom REST API, providing easy access to
AI-powered image editing, background removal, and image enhancement features.

Basic Usage:
    >>> from photoroom import PhotoRoomClient
    >>> client = PhotoRoomClient()
    >>> result = client.remove_background("photo.jpg", bg_color="white")
    >>> result.save("output.png")

Async Usage:
    >>> import asyncio
    >>> from photoroom import PhotoRoomClient
    >>>
    >>> async def main():
    ...     async with PhotoRoomClient(async_mode=True) as client:
    ...         result = await client.remove_background("photo.jpg")
    ...         result.save("output.png")
    >>>
    >>> asyncio.run(main())
"""

__version__ = "0.1.0"
__author__ = "PhotoRoom"
__license__ = "MIT"

from .client import PhotoRoomClient
from .exceptions import (
    PhotoRoomAuthError,
    PhotoRoomBadRequest,
    PhotoRoomError,
    PhotoRoomPaymentError,
    PhotoRoomServerError,
    BatchError,
    BatchPartialFailureError,
)
from .types import (
    AccountInfo,
    ImageResponse,
    BatchItemResult,
    BatchProgress,
)
from .batch import BatchResult

__all__ = [
    # Main client
    "PhotoRoomClient",
    # Exceptions
    "PhotoRoomError",
    "PhotoRoomBadRequest",
    "PhotoRoomPaymentError",
    "PhotoRoomAuthError",
    "PhotoRoomServerError",
    "BatchError",
    "BatchPartialFailureError",
    # Response types
    "ImageResponse",
    "AccountInfo",
    # Batch types
    "BatchResult",
    "BatchItemResult",
    "BatchProgress",
    # Version
    "__version__",
]
