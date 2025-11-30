"""Unit tests for PhotoRoom client."""

import os
import pytest
import httpx
import respx

from photoroom import (
    PhotoRoomClient,
    PhotoRoomError,
    PhotoRoomBadRequest,
    PhotoRoomPaymentError,
    PhotoRoomAuthError,
)


@pytest.fixture
def api_key():
    """Provide test API key."""
    return "test_api_key_12345"


@pytest.fixture
def client(api_key):
    """Create PhotoRoom client for testing."""
    return PhotoRoomClient(api_key=api_key)


@pytest.fixture
async def async_client(api_key):
    """Create async PhotoRoom client for testing."""
    async with PhotoRoomClient(api_key=api_key, async_mode=True) as client:
        yield client


def test_client_initialization_with_key():
    """Test client initialization with explicit API key."""
    client = PhotoRoomClient(api_key="test_key")
    assert client.api_key == "test_key"
    assert not client.async_mode


def test_client_initialization_from_env(monkeypatch):
    """Test client initialization from environment variable."""
    monkeypatch.setenv("PHOTOROOM_API_KEY", "env_key")
    client = PhotoRoomClient()
    assert client.api_key == "env_key"


def test_client_initialization_no_key():
    """Test client initialization fails without API key."""
    # Clear environment variable if set
    if "PHOTOROOM_API_KEY" in os.environ:
        old_key = os.environ["PHOTOROOM_API_KEY"]
        del os.environ["PHOTOROOM_API_KEY"]
    else:
        old_key = None

    try:
        with pytest.raises(ValueError, match="No API key provided"):
            PhotoRoomClient()
    finally:
        # Restore environment variable
        if old_key is not None:
            os.environ["PHOTOROOM_API_KEY"] = old_key


def test_sync_context_manager(api_key):
    """Test sync context manager."""
    with PhotoRoomClient(api_key=api_key) as client:
        assert client.api_key == api_key


def test_sync_context_manager_wrong_mode(api_key):
    """Test that async client can't use sync context manager."""
    client = PhotoRoomClient(api_key=api_key, async_mode=True)
    with pytest.raises(ValueError, match="Cannot use sync context manager"):
        with client:
            pass


@respx.mock
def test_get_account_success(client):
    """Test successful account info retrieval."""
    # Mock successful response
    respx.get(f"{client.IMAGE_API_BASE_URL}/v2/account").mock(
        return_value=httpx.Response(
            200,
            json={
                "plan": "Plus",
                "images": {"available": 87, "subscription": 100},
            },
        )
    )

    account = client.get_account()
    assert account.plan == "Plus"
    assert account.images.available == 87
    assert account.images.subscription == 100


@respx.mock
def test_get_account_auth_error(client):
    """Test account info with auth error."""
    # Mock 403 error
    respx.get(f"{client.IMAGE_API_BASE_URL}/v2/account").mock(
        return_value=httpx.Response(
            403,
            json={"error": {"message": "Invalid API key"}},
        )
    )

    with pytest.raises(PhotoRoomAuthError, match="Invalid API key"):
        client.get_account()


@respx.mock
def test_error_handling_400(client):
    """Test 400 Bad Request error handling."""
    respx.post(f"{client.SDK_BASE_URL}/v1/segment").mock(
        return_value=httpx.Response(
            400,
            json={"detail": "Missing required field: image_file"},
        )
    )

    with pytest.raises(PhotoRoomBadRequest, match="Missing required field"):
        client.remove_background(b"fake_image_data")


@respx.mock
def test_error_handling_402(client):
    """Test 402 Payment Required error handling."""
    respx.post(f"{client.SDK_BASE_URL}/v1/segment").mock(
        return_value=httpx.Response(
            402,
            json={"error": {"detail": "Quota exceeded"}},
        )
    )

    with pytest.raises(PhotoRoomPaymentError, match="Quota exceeded"):
        client.remove_background(b"fake_image_data")


def test_headers_include_api_key(client):
    """Test that headers include API key."""
    headers = client._get_headers()
    assert headers["X-Api-Key"] == client.api_key


def test_client_cleanup_on_context_exit(api_key):
    """Test that client is properly cleaned up on context exit."""
    with PhotoRoomClient(api_key=api_key) as client:
        assert client._client is not None

    # After context exit, client should be closed
    assert client._client is None or client._client.is_closed


@respx.mock
def test_retry_on_500_error(api_key):
    """Test that client retries on 500 server error."""
    client = PhotoRoomClient(api_key=api_key, max_retries=2)

    # Mock first request to fail with 500, second to succeed
    route = respx.get(f"{client.IMAGE_API_BASE_URL}/v2/account")
    route.side_effect = [
        httpx.Response(500, json={"error": {"message": "Internal server error"}}),
        httpx.Response(
            200,
            json={
                "plan": "Plus",
                "images": {"available": 87, "subscription": 100},
            },
        ),
    ]

    # Should succeed after retry
    account = client.get_account()
    assert account.plan == "Plus"
    assert route.call_count == 2


@respx.mock
def test_retry_exhaustion(api_key):
    """Test that client gives up after max retries."""
    client = PhotoRoomClient(api_key=api_key, max_retries=2)

    route = respx.get(f"{client.IMAGE_API_BASE_URL}/v2/account")
    route.mock(
        return_value=httpx.Response(
            503,
            json={"error": {"message": "Service unavailable"}},
        )
    )

    # Should fail after exhausting retries
    # After max retries, the error should be parsed by _handle_response
    with pytest.raises(PhotoRoomError, match="Service unavailable"):
        client.get_account()

    # Should have retried max_retries + 1 times (initial + 2 retries)
    assert route.call_count == 3


@respx.mock
def test_no_retry_on_400_error(api_key):
    """Test that client does not retry on 400 errors."""
    client = PhotoRoomClient(api_key=api_key, max_retries=3)

    route = respx.get(f"{client.IMAGE_API_BASE_URL}/v2/account")
    route.mock(
        return_value=httpx.Response(
            400,
            json={"error": {"message": "Bad request"}},
        )
    )

    # Should fail immediately without retry
    with pytest.raises(PhotoRoomBadRequest):
        client.get_account()

    # Should only be called once (no retries)
    assert route.call_count == 1


@respx.mock
def test_retry_on_network_error(api_key):
    """Test that client retries on network errors."""
    client = PhotoRoomClient(api_key=api_key, max_retries=2)

    route = respx.get(f"{client.IMAGE_API_BASE_URL}/v2/account")
    route.side_effect = [
        httpx.ConnectError("Connection failed"),
        httpx.Response(
            200,
            json={
                "plan": "Plus",
                "images": {"available": 87, "subscription": 100},
            },
        ),
    ]

    # Should succeed after retry
    account = client.get_account()
    assert account.plan == "Plus"
    assert route.call_count == 2


def test_retry_config_initialization(api_key):
    """Test that retry config is properly initialized."""
    client = PhotoRoomClient(
        api_key=api_key,
        max_retries=5,
        retry_backoff=3.0,
        retry_on_status=[500, 502],
    )

    assert client.retry_config.max_retries == 5
    assert client.retry_config.backoff_factor == 3.0
    assert client.retry_config.retry_on_status == [500, 502]


@respx.mock
def test_custom_retry_status_codes(api_key):
    """Test that custom retry status codes are respected."""
    # Only retry on 500, not on 503
    client = PhotoRoomClient(
        api_key=api_key,
        max_retries=2,
        retry_on_status=[500],
    )

    # Mock 503 error
    route = respx.get(f"{client.IMAGE_API_BASE_URL}/v2/account")
    route.mock(
        return_value=httpx.Response(
            503,
            json={"error": {"message": "Service unavailable"}},
        )
    )

    # Should fail immediately without retry (503 not in retry list)
    # Error should be parsed by _handle_response
    with pytest.raises(PhotoRoomError, match="Service unavailable"):
        client.get_account()

    # Should only be called once (no retries for 503)
    assert route.call_count == 1
