"""PhotoRoom API Type Definitions and Response Models.

This module defines Pydantic models for API responses and type helpers.
"""

from typing import Any, Dict, Optional, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Pydantic is optional, provide fallback BaseModel
    class BaseModel:  # type: ignore
        """Fallback BaseModel when Pydantic is not installed."""

        def __init__(self, **kwargs: Any) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

        def dict(self) -> Dict[str, Any]:
            """Convert model to dictionary."""
            return {
                k: v
                for k, v in self.__dict__.items()
                if not k.startswith("_")
            }


class AccountImages(BaseModel):
    """Image quota information for account.

    Attributes:
        available: Number of images remaining in current quota
        subscription: Total number of images in subscription
    """

    available: int = Field(..., description="Number of images available")
    subscription: int = Field(
        ..., ge=0, description="Total images in subscription"
    )


class AccountInfo(BaseModel):
    """Account information response from /v2/account.

    Attributes:
        plan: Name of the pricing plan (e.g., "Plus", "Basic")
        images: Image quota information
    """

    plan: str = Field(..., description="Name of the pricing plan")
    images: AccountImages = Field(..., description="Image quota information")


class ImageResponse:
    """Response wrapper for image processing operations.

    Contains both the binary image data and metadata from response headers.

    Attributes:
        image_data: Binary image data (PNG, JPEG, or WebP)
        metadata: Dictionary containing response headers and metadata
    """

    def __init__(self, image_data: bytes, metadata: Optional[Dict[str, Any]] = None):
        """Initialize ImageResponse.

        Args:
            image_data: Binary image data
            metadata: Optional metadata dictionary with response headers
        """
        self.image_data = image_data
        self.metadata = metadata or {}

    @property
    def size(self) -> int:
        """Get the size of the image data in bytes.

        Returns:
            Size in bytes
        """
        return len(self.image_data)

    @property
    def size_kb(self) -> float:
        """Get the size of the image data in kilobytes.

        Returns:
            Size in KB
        """
        return len(self.image_data) / 1024

    @property
    def background_seed(self) -> Optional[int]:
        """Get the seed used for background generation.

        Returns:
            Seed value if available, None otherwise
        """
        seed = self.metadata.get("pr-ai-background-seed")
        if seed is not None:
            try:
                return int(seed)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def texts_detected(self) -> Optional[int]:
        """Get number of texts detected in image.

        Returns:
            Number of texts detected if available, None otherwise
        """
        texts = self.metadata.get("pr-texts-detected")
        if texts is not None:
            try:
                return int(texts)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def edit_further_url(self) -> Optional[str]:
        """Get URL to edit result in PhotoRoom web app.

        Returns:
            URL string if available, None otherwise
        """
        return self.metadata.get("pr-edit-further-url")

    @property
    def unsupported_attributes(self) -> Optional[str]:
        """Get list of unsupported attributes from request.

        Returns:
            Unsupported attributes string if available, None otherwise
        """
        return self.metadata.get("pr-unsupported-attributes")

    def save(self, file_path: str) -> None:
        """Save image data to file.

        Args:
            file_path: Path where image should be saved
        """
        from pathlib import Path

        Path(file_path).write_bytes(self.image_data)

    def __repr__(self) -> str:
        """String representation of ImageResponse."""
        size_kb = len(self.image_data) / 1024
        meta_keys = list(self.metadata.keys())
        return f"ImageResponse(size={size_kb:.1f}KB, metadata={meta_keys})"


# Type aliases for common parameter types
SizeSpec = Union[str, int]  # e.g., "1024x768", "preview", "full"
ColorSpec = str  # e.g., "red", "FF0000", "#FF0000EE"
PaddingMarginSpec = Union[int, float, str]  # e.g., 0.1, "30%", "100px"


# Batch processing types
BatchInput = Union[str, Path, bytes]  # File path, Path object, or binary data


@dataclass
class BatchItemResult:
    """Result of processing a single item in a batch.

    Attributes:
        index: Index of the item in the original batch
        input_file: Original input file path or identifier
        success: Whether the processing succeeded
        result: ImageResponse if successful, None otherwise
        error: Exception if failed, None otherwise
        output_file: Path where result was saved (if applicable)
    """

    index: int
    input_file: str
    success: bool
    result: Optional[ImageResponse] = None
    error: Optional[Exception] = None
    output_file: Optional[str] = None

    def __repr__(self) -> str:
        """String representation of BatchItemResult."""
        if self.success:
            size_info = f"{self.result.size_kb:.1f}KB" if self.result else "N/A"
            return f"BatchItemResult(index={self.index}, success=True, size={size_info})"
        else:
            error_msg = str(self.error)[:50] if self.error else "Unknown error"
            return f"BatchItemResult(index={self.index}, success=False, error={error_msg})"


@dataclass
class BatchProgress:
    """Progress information for batch processing.

    Attributes:
        total: Total number of items to process
        completed: Number of items completed
        successful: Number of items that succeeded
        failed: Number of items that failed
        elapsed_seconds: Elapsed time in seconds
        estimated_remaining_seconds: Estimated remaining time (None if unknown)
    """

    total: int
    completed: int = 0
    successful: int = 0
    failed: int = 0
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: Optional[float] = None

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage (0-100).

        Returns:
            Progress as percentage
        """
        if self.total == 0:
            return 100.0
        return (self.completed / self.total) * 100

    @property
    def is_complete(self) -> bool:
        """Check if batch is complete.

        Returns:
            True if all items processed
        """
        return self.completed >= self.total

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0-1).

        Returns:
            Success rate as decimal (0-1)
        """
        if self.completed == 0:
            return 0.0
        return self.successful / self.completed

    def __repr__(self) -> str:
        """String representation of BatchProgress."""
        return (
            f"BatchProgress({self.completed}/{self.total} "
            f"[{self.progress_percent:.1f}%], "
            f"success={self.successful}, failed={self.failed})"
        )


# Type alias for progress callback
ProgressCallback = Callable[[BatchProgress], None]
