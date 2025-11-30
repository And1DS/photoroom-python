"""Integration tests with real PhotoRoom API.

These tests make real API calls using the sandbox API key.
Run with: pytest -m integration

WARNING: These tests consume API quota. Run sparingly!
"""

import pytest
from pathlib import Path

from photoroom import PhotoRoomClient, PhotoRoomAuthError


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# Sandbox API key (provided by user for testing)
SANDBOX_API_KEY = "sandbox_sk_pr_default_8bd14bd6fd16cadbf47050ab26978da6ec05545f"


# Path to test images
TEST_IMAGES_DIR = Path(__file__).parent.parent / "images"


@pytest.fixture
def client():
    """Create PhotoRoom client with sandbox API key."""
    return PhotoRoomClient(api_key=SANDBOX_API_KEY)


@pytest.mark.skip(reason="Conserving API quota - only run when needed")
def test_get_account_real(client):
    """Test getting real account information.

    This test makes a real API call to verify authentication works.
    """
    account = client.get_account()

    # Verify we got account info
    assert account.plan is not None
    assert hasattr(account.images, 'available')
    assert hasattr(account.images, 'subscription')

    print(f"Account plan: {account.plan}")
    print(f"Images available: {account.images.available}/{account.images.subscription}")


@pytest.mark.skip(reason="Conserving API quota - only run when needed")
def test_remove_background_real(client, tmp_path):
    """Test real background removal with test image.

    This test makes a real API call to remove background from a test image.
    Only run this when you need to verify the endpoint works!
    """
    # Use a test image
    test_image = TEST_IMAGES_DIR / "shoes.png"

    if not test_image.exists():
        pytest.skip(f"Test image not found: {test_image}")

    # Remove background with white color
    result = client.remove_background(
        str(test_image),
        bg_color="white",
        size="preview"  # Use preview size to save quota
    )

    # Verify we got a result
    assert result.image_data is not None
    assert len(result.image_data) > 0

    # Save result for manual inspection
    output_path = tmp_path / "test_remove_bg_result.png"
    result.save(str(output_path))

    assert output_path.exists()
    print(f"Result saved to: {output_path}")
    print(f"Result size: {len(result.image_data) / 1024:.1f} KB")


@pytest.mark.skip(reason="Conserving API quota - only run when needed")
def test_edit_image_real(client, tmp_path):
    """Test real image editing with AI background.

    This test makes a real API call to edit an image with an AI background.
    Only run this when you need to verify the endpoint works!
    """
    # Use a test image
    test_image = TEST_IMAGES_DIR / "shoes.png"

    if not test_image.exists():
        pytest.skip(f"Test image not found: {test_image}")

    # Edit image with white background and soft shadow
    result = client.edit_image(
        image_file=str(test_image),
        background_color="white",
        shadow_mode="ai.soft",
        padding=0.1,
        export_format="png",
    )

    # Verify we got a result
    assert result.image_data is not None
    assert len(result.image_data) > 0

    # Check metadata
    if result.edit_further_url:
        print(f"Edit further URL: {result.edit_further_url}")

    # Save result for manual inspection
    output_path = tmp_path / "test_edit_result.png"
    result.save(str(output_path))

    assert output_path.exists()
    print(f"Result saved to: {output_path}")
    print(f"Result size: {len(result.image_data) / 1024:.1f} KB")
    print(f"Image response: {result}")


def test_invalid_api_key():
    """Test that invalid API key raises authentication error.

    This makes a real API call but should fail immediately,
    so it doesn't waste quota.
    """
    client = PhotoRoomClient(api_key="invalid_key_12345")

    with pytest.raises(PhotoRoomAuthError):
        client.get_account()


# Note for running integration tests:
#
# To run ALL integration tests (WARNING: consumes API quota):
#   pytest -m integration
#
# To run a specific integration test:
#   pytest tests/test_integration.py::test_get_account_real -m integration
#
# To run with unskip:
#   pytest -m integration --runxfail
