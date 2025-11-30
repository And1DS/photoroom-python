"""Image validation and preprocessing for PhotoRoom API.

This module provides validation and preprocessing utilities for images
before uploading to the PhotoRoom API.
"""

import io
from pathlib import Path
from typing import Optional, Tuple, Union

# Pillow is optional for auto-resize functionality
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


# PhotoRoom API limits
MAX_IMAGE_SIZE_MB = 30
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

# Resolution limits
MAX_DIMENSION_PIXELS = 5000  # Maximum pixels on widest side
RECOMMENDED_MAX_MEGAPIXELS = 25  # Recommended max for optimal performance

# Upscale mode-specific limits
UPSCALE_FAST_MAX_DIMENSION = 1000  # ai.fast mode max input size
UPSCALE_SLOW_MAX_DIMENSION = 512   # ai.slow mode max input size

# Supported image formats (PhotoRoom API input formats)
SUPPORTED_FORMATS = {
    "jpeg", "jpg", "png", "webp"
}

# Additional formats that can be auto-converted (requires Pillow)
CONVERTIBLE_FORMATS = {
    "heic", "heif", "tiff", "tif", "bmp", "gif", "ico"
}


class ImageValidationError(Exception):
    """Exception raised when image validation fails."""

    pass


def validate_image_size(image_data: bytes, max_size_mb: int = MAX_IMAGE_SIZE_MB) -> None:
    """Validate that image size is within limits.

    Args:
        image_data: Binary image data
        max_size_mb: Maximum allowed size in MB

    Raises:
        ImageValidationError: If image exceeds size limit
    """
    size_bytes = len(image_data)
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > max_size_mb:
        raise ImageValidationError(
            f"Image size ({size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB). "
            f"Consider using auto_resize=True to automatically resize large images."
        )


def validate_image_format(file_path: Union[str, Path]) -> str:
    """Validate image format is supported.

    Args:
        file_path: Path to image file

    Returns:
        Detected image format (lowercase)

    Raises:
        ImageValidationError: If format is not supported
    """
    path = Path(file_path)
    extension = path.suffix.lower().lstrip(".")

    if not extension:
        raise ImageValidationError(
            f"Could not determine image format for: {file_path}"
        )

    if extension not in SUPPORTED_FORMATS:
        raise ImageValidationError(
            f"Unsupported image format: {extension}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    return extension


def get_image_dimensions(image_data: bytes) -> Optional[Tuple[int, int]]:
    """Get image dimensions from binary data.

    Args:
        image_data: Binary image data

    Returns:
        Tuple of (width, height) or None if cannot determine

    Note:
        Returns None if Pillow is not available or if image cannot be read.
        This allows validation to gracefully skip dimension checks when
        image format is unrecognized or data is invalid.
    """
    if not PILLOW_AVAILABLE:
        return None

    try:
        img = Image.open(io.BytesIO(image_data))
        return img.size
    except Exception:
        # Cannot read dimensions - return None to skip dimension validation
        # This can happen with invalid image data or unsupported formats
        return None


def validate_image_resolution(
    image_data: bytes,
    max_dimension: int = MAX_DIMENSION_PIXELS
) -> None:
    """Validate that image resolution doesn't exceed maximum dimension.

    Args:
        image_data: Binary image data
        max_dimension: Maximum pixels on widest side (default: 5000)

    Raises:
        ImageValidationError: If image exceeds dimension limit
    """
    dimensions = get_image_dimensions(image_data)

    if dimensions is None:
        # Cannot validate without Pillow
        return

    width, height = dimensions
    max_side = max(width, height)

    if max_side > max_dimension:
        raise ImageValidationError(
            f"Image resolution ({width}x{height}) exceeds maximum dimension "
            f"of {max_dimension}px on widest side (current: {max_side}px). "
            f"Consider using auto_resize=True to automatically resize large images."
        )


def validate_megapixels(
    image_data: bytes,
    max_mp: int = RECOMMENDED_MAX_MEGAPIXELS,
    warn_only: bool = True
) -> None:
    """Validate that image doesn't exceed recommended megapixel count.

    Args:
        image_data: Binary image data
        max_mp: Maximum recommended megapixels (default: 25)
        warn_only: If True, only warn instead of raising error

    Raises:
        ImageValidationError: If image exceeds MP limit and warn_only=False
    """
    dimensions = get_image_dimensions(image_data)

    if dimensions is None:
        return

    width, height = dimensions
    megapixels = (width * height) / 1_000_000

    if megapixels > max_mp:
        message = (
            f"Image resolution ({width}x{height}, {megapixels:.1f}MP) exceeds "
            f"recommended maximum of {max_mp}MP for optimal performance. "
            f"Consider resizing to improve processing speed."
        )

        if not warn_only:
            raise ImageValidationError(message)
        # Note: In production, this could use logging.warning()
        # For now, we just pass silently if warn_only=True


def validate_upscale_dimensions(
    image_data: bytes,
    mode: str
) -> None:
    """Validate dimensions for upscale mode.

    Args:
        image_data: Binary image data
        mode: Upscale mode ("ai.fast" or "ai.slow")

    Raises:
        ImageValidationError: If dimensions don't meet upscale requirements
    """
    dimensions = get_image_dimensions(image_data)

    if dimensions is None:
        return

    width, height = dimensions
    max_side = max(width, height)

    if mode == "ai.fast":
        max_allowed = UPSCALE_FAST_MAX_DIMENSION
    elif mode == "ai.slow":
        max_allowed = UPSCALE_SLOW_MAX_DIMENSION
    else:
        # Unknown upscale mode, skip validation
        return

    if max_side > max_allowed:
        raise ImageValidationError(
            f"Image resolution ({width}x{height}) exceeds maximum for {mode} upscale mode. "
            f"Maximum allowed: {max_allowed}x{max_allowed}px. Current: {max_side}px on widest side."
        )


def resize_image(
    image_data: bytes,
    max_size_mb: int = MAX_IMAGE_SIZE_MB,
    quality: int = 85,
) -> bytes:
    """Resize image to fit within size limit.

    Uses Pillow to resize the image while maintaining aspect ratio.

    Args:
        image_data: Binary image data
        max_size_mb: Target maximum size in MB
        quality: JPEG quality for resized image (1-100)

    Returns:
        Resized image as bytes

    Raises:
        ImageValidationError: If Pillow is not available or resize fails
    """
    if not PILLOW_AVAILABLE:
        raise ImageValidationError(
            "PIL/Pillow is required for auto-resize functionality. "
            "Install with: pip install Pillow"
        )

    try:
        # Open image
        img = Image.open(io.BytesIO(image_data))

        # Convert RGBA to RGB if saving as JPEG
        if img.mode == "RGBA":
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = rgb_img

        # Binary search for optimal size
        min_scale = 0.1
        max_scale = 1.0
        target_bytes = max_size_mb * 1024 * 1024

        while max_scale - min_scale > 0.05:
            scale = (min_scale + max_scale) / 2
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)

            # Resize
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save to bytes
            buffer = io.BytesIO()
            resized.save(buffer, format="JPEG", quality=quality, optimize=True)
            size = buffer.tell()

            if size <= target_bytes:
                min_scale = scale
            else:
                max_scale = scale

        # Final resize at optimal scale
        final_width = int(img.width * min_scale)
        final_height = int(img.height * min_scale)
        resized = img.resize((final_width, final_height), Image.Resampling.LANCZOS)

        # Save to bytes
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

        return buffer.read()

    except Exception as e:
        raise ImageValidationError(f"Failed to resize image: {e}")


def convert_to_supported_format(
    image_data: bytes,
    target_format: str = "webp",
    quality: int = 90
) -> bytes:
    """Convert image to a supported format.

    Converts unsupported image formats (HEIC, TIFF, BMP, etc.) to a
    PhotoRoom-supported format (WebP, PNG, or JPEG).

    Args:
        image_data: Binary image data
        target_format: Target format - "webp" (default), "png", or "jpeg"/"jpg"
        quality: Quality for lossy formats (1-100, default: 90)

    Returns:
        Converted image as bytes

    Raises:
        ImageValidationError: If conversion fails or Pillow not available
    """
    if not PILLOW_AVAILABLE:
        raise ImageValidationError(
            "PIL/Pillow is required for format conversion. "
            "Install with: pip install Pillow"
        )

    try:
        # Open image (Pillow supports many formats)
        img = Image.open(io.BytesIO(image_data))

        # Normalize target format
        target_format = target_format.lower()
        if target_format == "jpg":
            target_format = "jpeg"

        # Convert RGBA to RGB for JPEG (doesn't support transparency)
        if target_format == "jpeg" and img.mode in ("RGBA", "LA", "P"):
            # Create white background
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            # Paste image with alpha channel as mask
            if img.mode in ("RGBA", "LA"):
                rgb_img.paste(img, mask=img.split()[-1])
            else:
                rgb_img.paste(img)
            img = rgb_img

        # Save to target format
        buffer = io.BytesIO()
        save_kwargs = {"format": target_format.upper()}

        # Add quality/optimization for lossy formats
        if target_format in ["jpeg", "webp"]:
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif target_format == "png":
            save_kwargs["optimize"] = True

        img.save(buffer, **save_kwargs)
        buffer.seek(0)

        return buffer.read()

    except Exception as e:
        raise ImageValidationError(f"Failed to convert image format: {e}")


def validate_and_prepare_image(
    image_data: bytes,
    file_path: Optional[Union[str, Path]] = None,
    auto_resize: bool = False,
    auto_convert: bool = False,
    validate: bool = True,
    max_dimension: Optional[int] = None,
) -> bytes:
    """Validate and optionally resize/convert image before upload.

    Args:
        image_data: Binary image data
        file_path: Optional file path for format validation
        auto_resize: Automatically resize if image exceeds size/dimension limits
        auto_convert: Automatically convert unsupported formats to WebP
        validate: Perform validation checks
        max_dimension: Override maximum dimension (default: 5000px)

    Returns:
        Processed image data (potentially converted/resized)

    Raises:
        ImageValidationError: If validation fails and auto-fix is disabled
    """
    if not validate:
        return image_data

    # Check for empty data
    if not image_data or len(image_data) == 0:
        raise ImageValidationError("Image data is empty")

    # Step 1: Validate and potentially convert format
    if file_path:
        path = Path(file_path)
        extension = path.suffix.lower().lstrip(".")

        if extension in SUPPORTED_FORMATS:
            # Format is already supported
            pass
        elif extension in CONVERTIBLE_FORMATS:
            # Format can be converted
            if auto_convert:
                image_data = convert_to_supported_format(
                    image_data,
                    target_format="webp",
                    quality=90
                )
            else:
                raise ImageValidationError(
                    f"Unsupported image format: {extension}. "
                    f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}. "
                    f"Enable auto_convert=True to automatically convert {extension} to WebP."
                )
        else:
            # Unknown format
            raise ImageValidationError(
                f"Unknown image format: {extension}. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )

    # Step 2: Validate resolution
    needs_resize_for_dimension = False
    try:
        validate_image_resolution(image_data, max_dimension or MAX_DIMENSION_PIXELS)
    except ImageValidationError:
        if auto_resize:
            needs_resize_for_dimension = True
        else:
            raise

    # Step 3: Validate file size
    needs_resize_for_size = False
    try:
        validate_image_size(image_data)
    except ImageValidationError:
        if auto_resize:
            needs_resize_for_size = True
        else:
            raise

    # Step 4: Perform resize if needed
    if needs_resize_for_dimension or needs_resize_for_size:
        # Resize to meet both size and dimension constraints
        dimensions = get_image_dimensions(image_data)
        if dimensions:
            width, height = dimensions
            max_allowed = max_dimension or MAX_DIMENSION_PIXELS
            max_side = max(width, height)

            # Calculate scale factor for dimension constraint
            if max_side > max_allowed:
                dimension_scale = max_allowed / max_side
            else:
                dimension_scale = 1.0

            # Resize with dimension constraint
            if dimension_scale < 1.0:
                # Need to resize for dimensions
                try:
                    img = Image.open(io.BytesIO(image_data))
                    new_width = int(width * dimension_scale)
                    new_height = int(height * dimension_scale)
                    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    # Save with appropriate format
                    buffer = io.BytesIO()
                    if img.mode in ("RGBA", "LA"):
                        # Use PNG for transparency
                        resized.save(buffer, format="PNG", optimize=True)
                    else:
                        # Use JPEG for photos
                        if resized.mode in ("RGBA", "LA", "P"):
                            resized = resized.convert("RGB")
                        resized.save(buffer, format="JPEG", quality=85, optimize=True)

                    buffer.seek(0)
                    image_data = buffer.read()
                except Exception:
                    pass  # Fall through to size-based resize

            # Check if still need size-based resize
            try:
                validate_image_size(image_data)
            except ImageValidationError:
                # Still too large, use size-based resize
                image_data = resize_image(image_data)

    # Step 5: Validate megapixels (warning only)
    validate_megapixels(image_data, warn_only=True)

    return image_data
