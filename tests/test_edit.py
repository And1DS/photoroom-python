"""Unit tests for image editing endpoint."""

import pytest
import httpx
import respx

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
def test_edit_image_with_file(client, fake_image_bytes):
    """Test image editing with file upload (POST)."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(
            200,
            content=b"edited_image_data",
            headers={
                "content-type": "image/png",
                "pr-ai-background-seed": "12345",
            },
        )
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        background_color="white"
    )

    assert isinstance(result, ImageResponse)
    assert result.image_data == b"edited_image_data"
    assert result.background_seed == 12345


@respx.mock
def test_edit_image_with_url(client):
    """Test image editing with URL (GET)."""
    respx.get(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(
            200,
            content=b"edited_image_data",
        )
    )

    result = client.edit_image(
        image_url="https://example.com/image.jpg",
        background_color="blue"
    )

    assert isinstance(result, ImageResponse)


@respx.mock
def test_edit_image_ai_background(client, fake_image_bytes):
    """Test image editing with AI-generated background."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(
            200,
            content=b"edited_image_data",
            headers={"pr-ai-background-seed": "67890"},
        )
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        background_prompt="on a beach at sunset"
    )

    assert result.background_seed == 67890


@respx.mock
def test_edit_image_with_shadow(client, fake_image_bytes):
    """Test image editing with shadow generation."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(200, content=b"result")
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        shadow_mode="ai.soft"
    )

    assert isinstance(result, ImageResponse)


@respx.mock
def test_edit_image_with_lighting(client, fake_image_bytes):
    """Test image editing with lighting adjustment."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(200, content=b"result")
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        lighting_mode="ai.auto"
    )

    assert isinstance(result, ImageResponse)


@respx.mock
def test_edit_image_text_removal(client, fake_image_bytes):
    """Test image editing with text removal."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(
            200,
            content=b"result",
            headers={"pr-texts-detected": "3"},
        )
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        text_removal_mode="ai.artificial",
        remove_background=False
    )

    assert result.texts_detected == 3


@respx.mock
def test_edit_image_upscale(client, fake_image_bytes):
    """Test image editing with upscaling."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(200, content=b"upscaled")
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        upscale_mode="ai.fast"
    )

    assert isinstance(result, ImageResponse)


@respx.mock
def test_edit_image_beautify(client, fake_image_bytes):
    """Test image editing with beautify mode."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(200, content=b"beautified")
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        beautify_mode="ai.auto"
    )

    assert isinstance(result, ImageResponse)


@respx.mock
def test_edit_image_uncrop(client, fake_image_bytes):
    """Test image editing with uncrop mode."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(200, content=b"uncropped")
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        uncrop_mode="ai.auto"
    )

    assert isinstance(result, ImageResponse)


@respx.mock
def test_edit_image_padding_margin(client, fake_image_bytes):
    """Test image editing with padding and margin."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(200, content=b"result")
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        padding=0.1,
        margin="30%",
        padding_top="50px"
    )

    assert isinstance(result, ImageResponse)


@respx.mock
def test_edit_image_output_size(client, fake_image_bytes):
    """Test image editing with custom output size."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(200, content=b"result")
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        output_size="1024x768"
    )

    assert isinstance(result, ImageResponse)


@respx.mock
def test_edit_image_export_formats(client, fake_image_bytes):
    """Test different export formats."""
    formats = ["png", "jpeg", "jpg", "webp"]

    for fmt in formats:
        respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
            return_value=httpx.Response(200, content=b"result")
        )

        result = client.edit_image(
            image_file=fake_image_bytes,
            export_format=fmt
        )

        assert isinstance(result, ImageResponse)


@respx.mock
def test_edit_image_segmentation(client, fake_image_bytes):
    """Test image editing with custom segmentation."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(200, content=b"result")
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        segmentation_prompt="keep the product",
        segmentation_mode="keepSalientObject"
    )

    assert isinstance(result, ImageResponse)


@respx.mock
def test_edit_image_no_image_error(client):
    """Test that error is raised when no image provided."""
    with pytest.raises(ValueError, match="Either image_file or image_url"):
        client.edit_image()


@respx.mock
def test_edit_image_both_image_error(client, fake_image_bytes):
    """Test that error is raised when both image_file and image_url provided."""
    with pytest.raises(ValueError, match="Cannot provide both"):
        client.edit_image(
            image_file=fake_image_bytes,
            image_url="https://example.com/image.jpg"
        )


@respx.mock
def test_edit_image_saves_to_file(client, fake_image_bytes, tmp_path):
    """Test that edited image can be saved to file."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(200, content=b"edited_image")
    )

    output_path = tmp_path / "edited.png"
    result = client.edit_image(
        image_file=fake_image_bytes,
        background_color="white",
        output_file=str(output_path)
    )

    assert output_path.exists()
    assert output_path.read_bytes() == b"edited_image"


@respx.mock
def test_edit_image_edit_further_url(client, fake_image_bytes):
    """Test that edit further URL is captured."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(
            200,
            content=b"result",
            headers={"pr-edit-further-url": "https://photoroom.com/edit/xyz"},
        )
    )

    result = client.edit_image(image_file=fake_image_bytes)

    assert result.edit_further_url == "https://photoroom.com/edit/xyz"


@respx.mock
def test_edit_image_unsupported_attributes(client, fake_image_bytes):
    """Test that unsupported attributes are captured."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(
            200,
            content=b"result",
            headers={
                "pr-unsupported-attributes": "Unsupported attributes: foo.bar"
            },
        )
    )

    result = client.edit_image(image_file=fake_image_bytes)

    assert "foo.bar" in result.unsupported_attributes


@respx.mock
def test_edit_image_complex_scenario(client, fake_image_bytes):
    """Test complex editing scenario with multiple parameters."""
    respx.post(f"{client.IMAGE_API_BASE_URL}/v2/edit").mock(
        return_value=httpx.Response(
            200,
            content=b"complex_result",
            headers={
                "pr-ai-background-seed": "99999",
                "content-type": "image/png",
            },
        )
    )

    result = client.edit_image(
        image_file=fake_image_bytes,
        background_prompt="professional studio",
        shadow_mode="ai.soft",
        lighting_mode="ai.auto",
        padding=0.15,
        margin="5%",
        export_format="png",
        export_dpi=300,
        output_size="2048x2048"
    )

    assert isinstance(result, ImageResponse)
    assert result.background_seed == 99999
