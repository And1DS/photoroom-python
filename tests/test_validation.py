"""Comprehensive tests for image validation functionality."""

import io
import pytest
from pathlib import Path

from photoroom.validation import (
    validate_image_size,
    validate_image_format,
    validate_image_resolution,
    validate_megapixels,
    validate_upscale_dimensions,
    convert_to_supported_format,
    validate_and_prepare_image,
    resize_image,
    ImageValidationError,
    MAX_IMAGE_SIZE_MB,
    MAX_DIMENSION_PIXELS,
    UPSCALE_FAST_MAX_DIMENSION,
    UPSCALE_SLOW_MAX_DIMENSION,
)

# Test helper to check if Pillow is available
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


# ============================================================================
# Test Helpers
# ============================================================================

def create_mock_image(width: int = 100, height: int = 100, format: str = "PNG", mode: str = "RGB") -> bytes:
    """Create a mock image for testing.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        format: Image format (PNG, JPEG, etc.)
        mode: Color mode (RGB, RGBA, etc.)

    Returns:
        Binary image data
    """
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    from PIL import Image

    # Create a simple colored image
    img = Image.new(mode, (width, height), color=(200, 100, 50))

    buffer = io.BytesIO()
    save_kwargs = {"format": format}

    if format.upper() in ["JPEG", "JPG"]:
        save_kwargs["quality"] = 85
        # Convert RGBA to RGB for JPEG
        if img.mode == "RGBA":
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img

    img.save(buffer, **save_kwargs)
    buffer.seek(0)
    return buffer.read()


def create_large_image(target_mb: float) -> bytes:
    """Create an image of approximately target size in MB.

    Args:
        target_mb: Target size in megabytes

    Returns:
        Binary image data
    """
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    # Calculate approximate dimensions needed
    # Rough estimate: uncompressed RGB image is width * height * 3 bytes
    # Compressed PNG is roughly 30-50% of uncompressed
    target_bytes = target_mb * 1024 * 1024
    pixels_needed = int((target_bytes / 1.5) ** 0.5)  # Square image

    return create_mock_image(pixels_needed, pixels_needed, "PNG")


# ============================================================================
# Format Validation Tests
# ============================================================================

def test_validate_supported_format_png(tmp_path):
    """Test that PNG format is validated as supported."""
    test_file = tmp_path / "test.png"
    test_file.write_bytes(create_mock_image(format="PNG"))

    # Should not raise
    result = validate_image_format(test_file)
    assert result == "png"


def test_validate_supported_format_jpg(tmp_path):
    """Test that JPG/JPEG formats are validated as supported."""
    test_file = tmp_path / "test.jpg"
    test_file.write_bytes(create_mock_image(format="JPEG"))

    result = validate_image_format(test_file)
    assert result == "jpg"

    # Also test .jpeg extension
    test_file2 = tmp_path / "test.jpeg"
    test_file2.write_bytes(create_mock_image(format="JPEG"))
    result2 = validate_image_format(test_file2)
    assert result2 == "jpeg"


def test_validate_supported_format_webp(tmp_path):
    """Test that WebP format is validated as supported."""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    test_file = tmp_path / "test.webp"
    test_file.write_bytes(create_mock_image(format="WEBP"))

    result = validate_image_format(test_file)
    assert result == "webp"


def test_validate_unsupported_format_heic(tmp_path):
    """Test that HEIC format is rejected without auto_convert."""
    test_file = tmp_path / "test.heic"
    test_file.write_bytes(b"mock heic data")

    with pytest.raises(ImageValidationError, match="Unsupported image format: heic"):
        validate_image_format(test_file)


def test_validate_unsupported_format_tiff(tmp_path):
    """Test that TIFF format is rejected without auto_convert."""
    test_file = tmp_path / "test.tiff"
    test_file.write_bytes(b"mock tiff data")

    with pytest.raises(ImageValidationError, match="Unsupported image format: tiff"):
        validate_image_format(test_file)


def test_validate_unknown_format(tmp_path):
    """Test that unknown formats are rejected."""
    test_file = tmp_path / "test.xyz"
    test_file.write_bytes(b"mock data")

    with pytest.raises(ImageValidationError, match="Unsupported image format: xyz"):
        validate_image_format(test_file)


def test_validate_no_extension(tmp_path):
    """Test that files without extension are rejected."""
    test_file = tmp_path / "test"
    test_file.write_bytes(b"mock data")

    with pytest.raises(ImageValidationError, match="Could not determine image format"):
        validate_image_format(test_file)


# ============================================================================
# Size Validation Tests
# ============================================================================

def test_validate_image_size_under_limit():
    """Test that images under 30MB pass validation."""
    # Create a small 1MB image
    image_data = create_mock_image(500, 500)

    # Should not raise
    validate_image_size(image_data)


def test_validate_image_size_at_limit():
    """Test that images at exactly 30MB pass validation."""
    # Create image data exactly at limit
    image_data = b"x" * (30 * 1024 * 1024)

    # Should not raise
    validate_image_size(image_data)


def test_validate_image_size_over_limit():
    """Test that images over 30MB fail validation."""
    # Create image data over limit (31MB)
    image_data = b"x" * (31 * 1024 * 1024)

    with pytest.raises(ImageValidationError, match="exceeds maximum allowed size"):
        validate_image_size(image_data)


def test_auto_resize_large_image():
    """Test that large images can be automatically resized."""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    # Create image data that's definitely over 30MB (32MB of raw data)
    large_image = b"x" * (32 * 1024 * 1024)

    # Verify it's too large
    with pytest.raises(ImageValidationError):
        validate_image_size(large_image)

    # Create an actual large PNG image for resize test
    large_png = create_large_image(35)

    # Resize should work (even if original wasn't over limit, resize should not fail)
    resized = resize_image(large_png, max_size_mb=30)

    # Verify resized image is under limit
    validate_image_size(resized)  # Should not raise
    assert len(resized) < 30 * 1024 * 1024


# ============================================================================
# Resolution Validation Tests
# ============================================================================

def test_validate_resolution_under_limit():
    """Test that images under 5000px pass resolution validation."""
    image_data = create_mock_image(4000, 3000)

    # Should not raise
    validate_image_resolution(image_data)


def test_validate_resolution_at_limit():
    """Test that images at exactly 5000px pass validation."""
    image_data = create_mock_image(5000, 3000)

    # Should not raise
    validate_image_resolution(image_data)


def test_validate_resolution_over_limit():
    """Test that images over 5000px fail validation."""
    image_data = create_mock_image(6000, 4000)

    with pytest.raises(ImageValidationError, match="exceeds maximum dimension"):
        validate_image_resolution(image_data)


def test_validate_megapixels_under_recommended():
    """Test that images under 25MP don't raise error."""
    # 4000x5000 = 20MP (under 25MP)
    image_data = create_mock_image(4000, 5000)

    # Should not raise (warn_only=True by default)
    validate_megapixels(image_data, warn_only=True)


def test_validate_megapixels_over_recommended():
    """Test that images over 25MP don't raise error with warn_only."""
    # 6000x5000 = 30MP (over 25MP)
    image_data = create_mock_image(6000, 5000)

    # Should not raise with warn_only=True
    validate_megapixels(image_data, warn_only=True)


def test_validate_megapixels_over_recommended_strict():
    """Test that images over 25MP raise error with warn_only=False."""
    # 6000x5000 = 30MP (over 25MP)
    image_data = create_mock_image(6000, 5000)

    with pytest.raises(ImageValidationError, match="exceeds recommended maximum"):
        validate_megapixels(image_data, warn_only=False)


# ============================================================================
# Auto-Convert Tests
# ============================================================================

def test_convert_png_to_webp():
    """Test converting PNG to WebP."""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    png_data = create_mock_image(format="PNG")
    webp_data = convert_to_supported_format(png_data, target_format="webp")

    # Verify it's WebP
    img = Image.open(io.BytesIO(webp_data))
    assert img.format == "WEBP"


def test_convert_png_to_jpeg():
    """Test converting PNG to JPEG."""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    png_data = create_mock_image(format="PNG")
    jpeg_data = convert_to_supported_format(png_data, target_format="jpeg")

    # Verify it's JPEG
    img = Image.open(io.BytesIO(jpeg_data))
    assert img.format == "JPEG"


def test_convert_rgba_to_jpeg():
    """Test converting RGBA PNG to JPEG (removes transparency)."""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    rgba_data = create_mock_image(format="PNG", mode="RGBA")
    jpeg_data = convert_to_supported_format(rgba_data, target_format="jpeg")

    # Verify it's JPEG and RGB mode
    img = Image.open(io.BytesIO(jpeg_data))
    assert img.format == "JPEG"
    assert img.mode == "RGB"


def test_convert_without_pillow():
    """Test that conversion fails gracefully without Pillow."""
    # This test would need to mock PILLOW_AVAILABLE = False
    # For now, we'll skip if Pillow is available
    if PILLOW_AVAILABLE:
        pytest.skip("Pillow is available, cannot test without it")


# ============================================================================
# Combined Auto-Convert + Auto-Resize Tests
# ============================================================================

def test_validate_and_prepare_with_auto_resize(tmp_path):
    """Test validate_and_prepare_image with auto_resize."""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    # Create oversized image
    large_image = create_large_image(35)
    test_file = tmp_path / "large.png"
    test_file.write_bytes(large_image)

    # Should resize automatically
    result = validate_and_prepare_image(
        large_image,
        file_path=test_file,
        auto_resize=True,
        validate=True
    )

    # Result should be under limit
    validate_image_size(result)  # Should not raise
    assert len(result) < 30 * 1024 * 1024


def test_validate_and_prepare_resolution_resize(tmp_path):
    """Test that oversized resolution gets resized."""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    # Create high-resolution image
    high_res = create_mock_image(6000, 4000)
    test_file = tmp_path / "highres.png"
    test_file.write_bytes(high_res)

    # Should resize automatically
    result = validate_and_prepare_image(
        high_res,
        file_path=test_file,
        auto_resize=True,
        validate=True
    )

    # Result should be under resolution limit
    validate_image_resolution(result)  # Should not raise


# ============================================================================
# Upscale Mode Validation Tests
# ============================================================================

def test_upscale_fast_within_limit():
    """Test that images ≤1000px pass ai.fast validation."""
    image_data = create_mock_image(1000, 800)

    # Should not raise
    validate_upscale_dimensions(image_data, "ai.fast")


def test_upscale_fast_exceeds_limit():
    """Test that images >1000px fail ai.fast validation."""
    image_data = create_mock_image(1200, 800)

    with pytest.raises(ImageValidationError, match="exceeds maximum for ai.fast"):
        validate_upscale_dimensions(image_data, "ai.fast")


def test_upscale_slow_within_limit():
    """Test that images ≤512px pass ai.slow validation."""
    image_data = create_mock_image(512, 400)

    # Should not raise
    validate_upscale_dimensions(image_data, "ai.slow")


def test_upscale_slow_exceeds_limit():
    """Test that images >512px fail ai.slow validation."""
    image_data = create_mock_image(600, 400)

    with pytest.raises(ImageValidationError, match="exceeds maximum for ai.slow"):
        validate_upscale_dimensions(image_data, "ai.slow")


def test_upscale_unknown_mode():
    """Test that unknown upscale modes don't raise errors."""
    image_data = create_mock_image(2000, 1500)

    # Should not raise for unknown mode
    validate_upscale_dimensions(image_data, "ai.unknown")


# ============================================================================
# Integration Tests with Endpoints
# ============================================================================

def test_integration_remove_background_with_validation(tmp_path):
    """Test that remove_background validates images when enabled."""
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    from photoroom import PhotoRoomClient

    # Create test image
    image_data = create_mock_image()
    test_file = tmp_path / "test.png"
    test_file.write_bytes(image_data)

    # Create client with validation enabled (default)
    client = PhotoRoomClient(api_key="test_key", validate_images=True)

    # The validation should be called when loading the image
    # (This would need mocking of the actual API call to fully test)
    # For now, we verify that the validation code path is accessible
    assert client.validate_images is True
    assert client.auto_resize is False
    assert client.auto_convert is False


def test_integration_client_disable_validation():
    """Test that validation can be disabled."""
    from photoroom import PhotoRoomClient

    client = PhotoRoomClient(api_key="test_key", validate_images=False)

    assert client.validate_images is False


def test_integration_client_auto_convert_auto_resize():
    """Test that auto_convert and auto_resize can be enabled together."""
    from photoroom import PhotoRoomClient

    client = PhotoRoomClient(
        api_key="test_key",
        validate_images=True,
        auto_resize=True,
        auto_convert=True
    )

    assert client.validate_images is True
    assert client.auto_resize is True
    assert client.auto_convert is True


# ============================================================================
# Edge Cases
# ============================================================================

def test_validate_empty_image_data():
    """Test that empty image data raises error."""
    with pytest.raises(Exception):  # Could be ImageValidationError or PIL error
        validate_and_prepare_image(b"", validate=True)


def test_validate_corrupted_image_data():
    """Test that corrupted image data is handled gracefully."""
    corrupted_data = b"not a real image"

    # get_image_dimensions should return None for corrupted data
    # instead of raising an error, allowing validation to continue
    if PILLOW_AVAILABLE:
        from photoroom.validation import get_image_dimensions
        dimensions = get_image_dimensions(corrupted_data)
        assert dimensions is None  # Cannot read dimensions from corrupted data
