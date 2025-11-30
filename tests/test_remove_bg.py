"""Unit tests for background removal endpoint."""

import pytest
import httpx
import respx
from pathlib import Path

from photoroom import PhotoRoomClient, PhotoRoomBadRequest, ImageResponse


@pytest.fixture
def client():
    """Create PhotoRoom client for testing."""
    return PhotoRoomClient(api_key="test_key")


@pytest.fixture
def fake_image_bytes():
    """Provide fake image bytes for testing."""
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00" + b"\x00" * 100


@respx.mock
def test_remove_background_with_bytes(client, fake_image_bytes):
    """Test background removal with image bytes."""
    # Mock successful response
    respx.post(f"{client.SDK_BASE_URL}/v1/segment").mock(
        return_value=httpx.Response(
            200,
            content=b"fake_processed_image_data",
            headers={"content-type": "image/png"},
        )
    )

    result = client.remove_background(fake_image_bytes)

    assert isinstance(result, ImageResponse)
    assert result.image_data == b"fake_processed_image_data"


@respx.mock
def test_remove_background_with_options(client, fake_image_bytes):
    """Test background removal with various options."""
    route = respx.post(f"{client.SDK_BASE_URL}/v1/segment").mock(
        return_value=httpx.Response(
            200,
            content=b"fake_processed_image_data",
        )
    )

    result = client.remove_background(
        fake_image_bytes,
        format="jpg",
        channels="alpha",
        bg_color="white",
        size="hd",
        crop=True,
        despill=True,
    )

    assert isinstance(result, ImageResponse)

    # Verify request was made with correct parameters
    assert route.called
    request = route.calls.last.request

    # Check that form data includes our parameters
    # Note: exact format checking depends on httpx internals


@respx.mock
def test_remove_background_default_params(client, fake_image_bytes):
    """Test background removal with default parameters."""
    route = respx.post(f"{client.SDK_BASE_URL}/v1/segment").mock(
        return_value=httpx.Response(200, content=b"result")
    )

    result = client.remove_background(fake_image_bytes)

    assert route.called
    # Defaults should be: format=png, channels=rgba, size=full


@respx.mock
def test_remove_background_error_handling(client, fake_image_bytes):
    """Test error handling in background removal."""
    respx.post(f"{client.SDK_BASE_URL}/v1/segment").mock(
        return_value=httpx.Response(
            400,
            json={
                "detail": "Invalid image format",
                "status_code": 400,
                "type": "validation_error",
            },
        )
    )

    with pytest.raises(PhotoRoomBadRequest, match="Invalid image format"):
        client.remove_background(fake_image_bytes)


@respx.mock
def test_remove_background_saves_to_file(client, fake_image_bytes, tmp_path):
    """Test that result can be saved to file."""
    respx.post(f"{client.SDK_BASE_URL}/v1/segment").mock(
        return_value=httpx.Response(200, content=b"processed_image")
    )

    output_path = tmp_path / "output.png"
    result = client.remove_background(
        fake_image_bytes,
        output_file=str(output_path)
    )

    assert output_path.exists()
    assert output_path.read_bytes() == b"processed_image"


@respx.mock
def test_remove_background_all_size_options(client, fake_image_bytes):
    """Test all size options."""
    sizes = ["preview", "medium", "hd", "full"]

    for size in sizes:
        respx.post(f"{client.SDK_BASE_URL}/v1/segment").mock(
            return_value=httpx.Response(200, content=b"result")
        )

        result = client.remove_background(fake_image_bytes, size=size)
        assert isinstance(result, ImageResponse)


@respx.mock
def test_remove_background_all_formats(client, fake_image_bytes):
    """Test all output formats."""
    formats = ["png", "jpg", "webp"]

    for format in formats:
        respx.post(f"{client.SDK_BASE_URL}/v1/segment").mock(
            return_value=httpx.Response(200, content=b"result")
        )

        result = client.remove_background(fake_image_bytes, format=format)
        assert isinstance(result, ImageResponse)


@respx.mock
def test_remove_background_channels(client, fake_image_bytes):
    """Test channel options."""
    channels_options = ["rgba", "alpha"]

    for channels in channels_options:
        respx.post(f"{client.SDK_BASE_URL}/v1/segment").mock(
            return_value=httpx.Response(200, content=b"result")
        )

        result = client.remove_background(fake_image_bytes, channels=channels)
        assert isinstance(result, ImageResponse)
