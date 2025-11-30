"""PhotoRoom Account Endpoint.

This module provides methods for retrieving account information and quotas.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import PhotoRoomClient

from ..types import AccountInfo


def get_account(self: "PhotoRoomClient") -> AccountInfo:
    """Get account information and image quota.

    Returns account details including plan name and remaining images.
    Automatically retries on transient server errors.

    Returns:
        AccountInfo object with plan and quota information

    Raises:
        PhotoRoomAuthError: If API key is invalid (403)
        PhotoRoomBadRequest: If request is malformed (400)
        PhotoRoomServerError: If server error occurs (500)

    Examples:
        >>> client = PhotoRoomClient()
        >>> account = client.get_account()
        >>> print(f"Plan: {account.plan}")
        >>> print(f"Images available: {account.images.available}/{account.images.subscription}")
    """
    # Make request with retry logic
    response = self._make_request_with_retry(
        "GET",
        f"{self.IMAGE_API_BASE_URL}/v2/account",
    )

    # Handle response (expect JSON)
    data = self._handle_response(response, expect_json=True)

    # Parse into AccountInfo model
    return AccountInfo(**data)


async def aget_account(self: "PhotoRoomClient") -> AccountInfo:
    """Get account information and image quota (async).

    Async version of get_account(). Automatically retries on transient server errors.

    Returns:
        AccountInfo object with plan and quota information

    Raises:
        PhotoRoomAuthError: If API key is invalid (403)
        PhotoRoomBadRequest: If request is malformed (400)
        PhotoRoomServerError: If server error occurs (500)

    Examples:
        >>> async with PhotoRoomClient(async_mode=True) as client:
        ...     account = await client.get_account()
        ...     print(f"Plan: {account.plan}")
    """
    # Make request with retry logic
    response = await self._make_request_with_retry_async(
        "GET",
        f"{self.IMAGE_API_BASE_URL}/v2/account",
    )

    # Handle response (expect JSON)
    data = self._handle_response(response, expect_json=True)

    # Parse into AccountInfo model
    return AccountInfo(**data)
