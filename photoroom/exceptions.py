"""PhotoRoom API Exception Hierarchy.

This module defines custom exceptions for the PhotoRoom API, normalizing
different error response formats across endpoints.
"""

from typing import Any, Dict, Optional


class PhotoRoomError(Exception):
    """Base exception for all PhotoRoom API errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (if available)
        response_data: Raw response data from the API
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize PhotoRoomError.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            response_data: Raw response data from the API
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class PhotoRoomBadRequest(PhotoRoomError):
    """Exception raised for 400 Bad Request errors.

    Indicates invalid parameters or malformed requests.
    """

    pass


class PhotoRoomPaymentError(PhotoRoomError):
    """Exception raised for 402 Payment Required errors.

    Indicates insufficient credits or quota exceeded.
    """

    pass


class PhotoRoomAuthError(PhotoRoomError):
    """Exception raised for 403 Forbidden errors.

    Indicates authentication failure or invalid API key.
    """

    pass


class PhotoRoomServerError(PhotoRoomError):
    """Exception raised for 500 Internal Server Error.

    Indicates an error on PhotoRoom's servers.
    """

    pass


class BatchError(PhotoRoomError):
    """Exception raised for batch processing errors.

    Base exception for all batch-related errors.
    """

    pass


class BatchPartialFailureError(BatchError):
    """Exception raised when some items in a batch fail.

    Attributes:
        successful_count: Number of items that succeeded
        failed_count: Number of items that failed
        failures: List of (index, error) tuples for failed items
    """

    def __init__(
        self,
        message: str,
        successful_count: int,
        failed_count: int,
        failures: list = None,
    ) -> None:
        """Initialize BatchPartialFailureError.

        Args:
            message: Human-readable error message
            successful_count: Number of items that succeeded
            failed_count: Number of items that failed
            failures: List of (index, error) tuples for failed items
        """
        super().__init__(message)
        self.successful_count = successful_count
        self.failed_count = failed_count
        self.failures = failures or []

    def __str__(self) -> str:
        """Return string representation of the error."""
        return (
            f"{self.message} ({self.successful_count} succeeded, "
            f"{self.failed_count} failed)"
        )


def parse_error_response(
    status_code: int, response_data: Dict[str, Any]
) -> PhotoRoomError:
    """Parse API error response and return appropriate exception.

    Handles different error formats:
    - v2/edit format: {"error": {"message": "..."}}
    - v1/segment format: {"detail": "...", "status_code": ..., "type": "..."}

    Args:
        status_code: HTTP status code
        response_data: JSON response data from the API

    Returns:
        Appropriate PhotoRoomError subclass instance
    """
    # Extract error message from different formats
    message = "Unknown error"

    # Try v2/edit format: {"error": {"message": "..."}}
    if "error" in response_data:
        error_obj = response_data["error"]
        if isinstance(error_obj, dict):
            message = error_obj.get("message") or error_obj.get("detail", message)
        else:
            message = str(error_obj)

    # Try v1/segment format: {"detail": "...", "status_code": ..., "type": "..."}
    elif "detail" in response_data:
        message = response_data["detail"]

    # Map status code to exception class
    exception_map = {
        400: PhotoRoomBadRequest,
        402: PhotoRoomPaymentError,
        403: PhotoRoomAuthError,
        500: PhotoRoomServerError,
    }

    exception_class = exception_map.get(status_code, PhotoRoomError)
    return exception_class(
        message=message, status_code=status_code, response_data=response_data
    )
