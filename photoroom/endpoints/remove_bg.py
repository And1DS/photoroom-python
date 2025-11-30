"""PhotoRoom Background Removal Endpoint.

This module provides methods for removing backgrounds from images using
the /v1/segment endpoint (Basic plan).
"""

from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional, Union

if TYPE_CHECKING:
    from ..client import PhotoRoomClient

from ..types import ImageResponse
from ..utils import load_image_file


def remove_background(
    self: "PhotoRoomClient",
    image_file: Union[str, Path, bytes],
    format: Optional[Literal["png", "jpg", "webp"]] = "png",
    channels: Optional[Literal["rgba", "alpha"]] = "rgba",
    bg_color: Optional[str] = None,
    size: Optional[Literal["preview", "medium", "hd", "full"]] = "full",
    crop: Optional[bool] = False,
    despill: Optional[bool] = False,
    output_file: Optional[Union[str, Path]] = None,
) -> ImageResponse:
    """Remove background from an image.

    Uses the /v1/segment endpoint (Basic plan).

    Args:
        image_file: Path to image file or binary image data
        format: Output format - png, jpg, or webp. Default: png.
        channels: Output channels - rgba (color+alpha) or alpha only. Default: rgba.
        bg_color: Background color for transparent areas. Can be hex (FF0000) or
            color name (red, blue, etc.). If omitted, background is transparent.
        size: Output size - preview (0.25 MP), medium (1.5 MP), hd (4 MP), or
            full (36 MP). Default: full.
        crop: If True, crop image to cutout border (remove transparent pixels).
            Default: False.
        despill: If True, remove colored reflections from green screen. Default: False.
        output_file: Optional path to save result. If provided, image is saved
            to disk and ImageResponse is still returned.

    Returns:
        ImageResponse containing processed image and metadata

    Raises:
        FileNotFoundError: If image_file path doesn't exist
        PhotoRoomBadRequest: If parameters are invalid (400)
        PhotoRoomPaymentError: If quota exceeded (402)
        PhotoRoomAuthError: If API key is invalid (403)

    Examples:
        >>> client = PhotoRoomClient()
        >>> # Remove background with white fill
        >>> result = client.remove_background("photo.jpg", bg_color="white")
        >>> result.save("output.png")
        >>>
        >>> # Get alpha channel only, cropped
        >>> result = client.remove_background(
        ...     "photo.jpg",
        ...     channels="alpha",
        ...     crop=True
        ... )
    """
    client = self._get_client()

    # Load image file if path is provided
    if isinstance(image_file, (str, Path)):
        image_data = load_image_file(
            image_file,
            validate=self.validate_images,
            auto_resize=self.auto_resize,
            auto_convert=self.auto_convert,
        )
        filename = Path(image_file).name
    else:
        # For bytes input, validate if enabled
        if self.validate_images:
            from ..validation import validate_and_prepare_image
            image_data = validate_and_prepare_image(
                image_file,
                auto_resize=self.auto_resize,
                auto_convert=self.auto_convert,
                validate=True,
            )
        else:
            image_data = image_file
        filename = "image.jpg"

    # Build form data
    files = {
        "image_file": (filename, image_data, "image/jpeg"),
    }

    data = {}
    if format is not None:
        data["format"] = format
    if channels is not None:
        data["channels"] = channels
    if bg_color is not None:
        data["bg_color"] = bg_color
    if size is not None:
        data["size"] = size
    if crop is not None:
        data["crop"] = "true" if crop else "false"
    if despill is not None:
        data["despill"] = "true" if despill else "false"

    # Make request with retry logic
    response = self._make_request_with_retry(
        "POST",
        f"{self.SDK_BASE_URL}/v1/segment",
        files=files,
        data=data,
    )

    # Handle response
    result = self._handle_response(response, expect_json=False)

    # Save to file if requested
    if output_file is not None:
        result.save(output_file)

    return result


async def aremove_background(
    self: "PhotoRoomClient",
    image_file: Union[str, Path, bytes],
    format: Optional[Literal["png", "jpg", "webp"]] = "png",
    channels: Optional[Literal["rgba", "alpha"]] = "rgba",
    bg_color: Optional[str] = None,
    size: Optional[Literal["preview", "medium", "hd", "full"]] = "full",
    crop: Optional[bool] = False,
    despill: Optional[bool] = False,
    output_file: Optional[Union[str, Path]] = None,
) -> ImageResponse:
    """Remove background from an image (async).

    Async version of remove_background().

    Uses the /v1/segment endpoint (Basic plan).

    Args:
        image_file: Path to image file or binary image data
        format: Output format - png, jpg, or webp. Default: png.
        channels: Output channels - rgba (color+alpha) or alpha only. Default: rgba.
        bg_color: Background color for transparent areas. Can be hex (FF0000) or
            color name (red, blue, etc.). If omitted, background is transparent.
        size: Output size - preview (0.25 MP), medium (1.5 MP), hd (4 MP), or
            full (36 MP). Default: full.
        crop: If True, crop image to cutout border (remove transparent pixels).
            Default: False.
        despill: If True, remove colored reflections from green screen. Default: False.
        output_file: Optional path to save result. If provided, image is saved
            to disk and ImageResponse is still returned.

    Returns:
        ImageResponse containing processed image and metadata

    Raises:
        FileNotFoundError: If image_file path doesn't exist
        PhotoRoomBadRequest: If parameters are invalid (400)
        PhotoRoomPaymentError: If quota exceeded (402)
        PhotoRoomAuthError: If API key is invalid (403)

    Examples:
        >>> async with PhotoRoomClient(async_mode=True) as client:
        ...     result = await client.remove_background("photo.jpg", bg_color="white")
        ...     result.save("output.png")
    """
    client = self._get_client()

    # Load image file if path is provided
    if isinstance(image_file, (str, Path)):
        image_data = load_image_file(
            image_file,
            validate=self.validate_images,
            auto_resize=self.auto_resize,
            auto_convert=self.auto_convert,
        )
        filename = Path(image_file).name
    else:
        # For bytes input, validate if enabled
        if self.validate_images:
            from ..validation import validate_and_prepare_image
            image_data = validate_and_prepare_image(
                image_file,
                auto_resize=self.auto_resize,
                auto_convert=self.auto_convert,
                validate=True,
            )
        else:
            image_data = image_file
        filename = "image.jpg"

    # Build form data
    files = {
        "image_file": (filename, image_data, "image/jpeg"),
    }

    data = {}
    if format is not None:
        data["format"] = format
    if channels is not None:
        data["channels"] = channels
    if bg_color is not None:
        data["bg_color"] = bg_color
    if size is not None:
        data["size"] = size
    if crop is not None:
        data["crop"] = "true" if crop else "false"
    if despill is not None:
        data["despill"] = "true" if despill else "false"

    # Make request with retry logic
    response = await self._make_request_with_retry_async(
        "POST",
        f"{self.SDK_BASE_URL}/v1/segment",
        files=files,
        data=data,
    )

    # Handle response
    result = self._handle_response(response, expect_json=False)

    # Save to file if requested
    if output_file is not None:
        result.save(output_file)

    return result
