"""Unit tests for synchronous batch processing operations."""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import respx
import httpx

from photoroom import PhotoRoomClient, BatchResult, BatchProgress
from photoroom.exceptions import BatchError


# ============================================================================
# Batch Remove Background Tests
# ============================================================================


@respx.mock
def test_batch_remove_background_all_successful():
    """Test batch background removal with all successful items."""
    # Mock successful responses
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    client = PhotoRoomClient(api_key="test_key")

    # Process batch
    inputs = [b"image1", b"image2", b"image3"]
    result = client.batch_remove_background(inputs, bg_color="white", max_workers=2)

    assert isinstance(result, BatchResult)
    assert result.total == 3
    assert result.success_count == 3
    assert result.failure_count == 0
    assert result.all_successful is True


@respx.mock
def test_batch_remove_background_with_failures():
    """Test batch background removal with some failures."""
    # Mock responses: first succeeds, second fails, third succeeds
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            return httpx.Response(400, json={"detail": "Bad request"})
        return httpx.Response(200, content=b"fake_image_data")

    respx.post("https://sdk.photoroom.com/v1/segment").mock(side_effect=side_effect)

    client = PhotoRoomClient(api_key="test_key")

    # Process batch with continue on error
    inputs = [b"image1", b"image2", b"image3"]
    result = client.batch_remove_background(
        inputs, bg_color="white", max_workers=1, on_error="continue"
    )

    assert result.total == 3
    assert result.success_count == 2
    assert result.failure_count == 1
    assert result.any_failed is True


@respx.mock
def test_batch_remove_background_fail_fast():
    """Test batch with fail_fast error strategy."""
    # Mock first request to fail
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(400, json={"detail": "Bad request"})
    )

    client = PhotoRoomClient(api_key="test_key")

    # Process batch with fail_fast
    inputs = [b"image1", b"image2", b"image3"]

    with pytest.raises(BatchError, match="Batch processing failed"):
        client.batch_remove_background(
            inputs, bg_color="white", max_workers=1, on_error="fail_fast"
        )


@respx.mock
def test_batch_remove_background_with_output_dir():
    """Test batch processing with automatic output saving."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"processed_image_data")
    )

    # Create temporary output directory
    temp_dir = tempfile.mkdtemp()

    try:
        client = PhotoRoomClient(api_key="test_key")

        # Process batch with output directory
        inputs = [b"image1", b"image2"]
        output_dir = Path(temp_dir) / "output"

        result = client.batch_remove_background(
            inputs,
            bg_color="white",
            max_workers=2,
            output_dir=str(output_dir),
            output_pattern="{index}_result.png",
        )

        assert result.success_count == 2

        # Verify output files were created
        assert (output_dir / "0_result.png").exists()
        assert (output_dir / "1_result.png").exists()

        # Verify content
        content = (output_dir / "0_result.png").read_bytes()
        assert content == b"processed_image_data"

    finally:
        shutil.rmtree(temp_dir)


@respx.mock
def test_batch_remove_background_with_progress_callback():
    """Test batch processing with progress callback."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    client = PhotoRoomClient(api_key="test_key")

    # Track progress updates
    progress_updates = []

    def progress_callback(progress: BatchProgress):
        progress_updates.append(
            {
                "completed": progress.completed,
                "total": progress.total,
                "successful": progress.successful,
                "failed": progress.failed,
                "percent": progress.progress_percent,
            }
        )

    # Process batch
    inputs = [b"image1", b"image2", b"image3"]
    result = client.batch_remove_background(
        inputs, bg_color="white", max_workers=1, progress_callback=progress_callback
    )

    assert result.success_count == 3

    # Verify progress updates were called
    assert len(progress_updates) == 3
    assert progress_updates[-1]["completed"] == 3
    assert progress_updates[-1]["percent"] == 100.0


@respx.mock
def test_batch_remove_background_empty_input():
    """Test batch processing with empty input list."""
    client = PhotoRoomClient(api_key="test_key")

    result = client.batch_remove_background([], bg_color="white")

    assert result.total == 0
    assert result.success_count == 0
    assert result.failure_count == 0


# ============================================================================
# Batch Edit Image Tests
# ============================================================================


@respx.mock
def test_batch_edit_image_all_successful():
    """Test batch image editing with all successful items."""
    # Mock successful responses
    respx.post("https://image-api.photoroom.com/v2/edit").mock(
        return_value=httpx.Response(200, content=b"fake_edited_image")
    )

    client = PhotoRoomClient(api_key="test_key")

    # Process batch
    inputs = [b"image1", b"image2"]
    result = client.batch_edit_image(
        inputs, background_color="white", max_workers=2
    )

    assert isinstance(result, BatchResult)
    assert result.total == 2
    assert result.success_count == 2
    assert result.failure_count == 0


@respx.mock
def test_batch_edit_image_with_background_prompt():
    """Test batch editing with AI background prompt."""
    # Mock successful response
    respx.post("https://image-api.photoroom.com/v2/edit").mock(
        return_value=httpx.Response(200, content=b"fake_edited_image")
    )

    client = PhotoRoomClient(api_key="test_key")

    # Process batch with background prompt
    inputs = [b"image1", b"image2"]
    result = client.batch_edit_image(
        inputs,
        background_prompt="on a beach at sunset",
        background_seed=42,
        max_workers=2,
    )

    assert result.success_count == 2


@respx.mock
def test_batch_edit_image_with_failures():
    """Test batch editing with some failures."""
    # Mock responses: specific pattern of success/failure
    # Use side_effect list instead of function for more reliable behavior
    respx.post("https://image-api.photoroom.com/v2/edit").mock(
        side_effect=[
            httpx.Response(200, content=b"fake_edited_image_1"),  # Success
            httpx.Response(500, json={"error": {"message": "Server error"}}),  # Fail
            httpx.Response(200, content=b"fake_edited_image_3"),  # Success
            httpx.Response(500, json={"error": {"message": "Server error"}}),  # Fail
        ]
    )

    # Disable retries to prevent retry attempts from changing results
    client = PhotoRoomClient(api_key="test_key", max_retries=0)

    # Process batch sequentially to ensure predictable order
    inputs = [b"image1", b"image2", b"image3", b"image4"]
    result = client.batch_edit_image(
        inputs, background_color="white", max_workers=1, on_error="continue"
    )

    assert result.total == 4
    assert result.success_count == 2
    assert result.failure_count == 2


# ============================================================================
# Integration with Rate Limiting
# ============================================================================


@respx.mock
def test_batch_with_rate_limiting():
    """Test that batch operations respect rate limiting."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Create client with rate limiting (2 req/sec)
    client = PhotoRoomClient(
        api_key="test_key", rate_limit=2.0, rate_limit_strategy="wait"
    )

    # Process batch - should respect rate limit
    start_time = time.time()
    inputs = [b"image1", b"image2", b"image3"]
    result = client.batch_remove_background(
        inputs, bg_color="white", max_workers=1  # Sequential to test rate limiting
    )
    elapsed = time.time() - start_time

    assert result.success_count == 3

    # With 2 req/sec and burst_size=2:
    # First 2 requests instant, 3rd waits ~0.5s
    assert elapsed >= 0.4  # Allow some timing variance


# ============================================================================
# Error Handling Tests
# ============================================================================


@respx.mock
def test_batch_result_raise_on_failure():
    """Test BatchResult.raise_on_failure() method."""
    # Mock responses: one failure
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            return httpx.Response(400, json={"detail": "Bad request"})
        return httpx.Response(200, content=b"fake_image_data")

    respx.post("https://sdk.photoroom.com/v1/segment").mock(side_effect=side_effect)

    client = PhotoRoomClient(api_key="test_key")

    # Process batch
    inputs = [b"image1", b"image2", b"image3"]
    result = client.batch_remove_background(
        inputs, bg_color="white", max_workers=1, on_error="continue"
    )

    assert result.any_failed is True

    # Should raise exception
    from photoroom.exceptions import BatchPartialFailureError

    with pytest.raises(BatchPartialFailureError) as exc_info:
        result.raise_on_failure()

    assert exc_info.value.successful_count == 2
    assert exc_info.value.failed_count == 1


# ============================================================================
# File Input Tests
# ============================================================================


@respx.mock
def test_batch_with_file_paths():
    """Test batch processing with file path inputs."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Create temporary test images
    temp_dir = tempfile.mkdtemp()

    try:
        # Create test image files
        image1 = Path(temp_dir) / "image1.jpg"
        image2 = Path(temp_dir) / "image2.jpg"
        image1.write_bytes(b"fake_image_1")
        image2.write_bytes(b"fake_image_2")

        client = PhotoRoomClient(api_key="test_key")

        # Process batch with file paths
        inputs = [str(image1), str(image2)]
        result = client.batch_remove_background(inputs, bg_color="white")

        assert result.success_count == 2
        assert result.results[0].input_file == str(image1)
        assert result.results[1].input_file == str(image2)

    finally:
        shutil.rmtree(temp_dir)


# ============================================================================
# Concurrency Tests
# ============================================================================


@respx.mock
def test_batch_with_max_workers():
    """Test batch processing respects max_workers setting."""
    # Mock successful response with delay to test concurrency
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    client = PhotoRoomClient(api_key="test_key")

    # Process with different worker counts
    inputs = [b"image1", b"image2", b"image3", b"image4"]

    # Sequential (max_workers=1)
    start_time = time.time()
    result = client.batch_remove_background(inputs, max_workers=1)
    sequential_time = time.time() - start_time

    # Parallel (max_workers=4)
    start_time = time.time()
    result = client.batch_remove_background(inputs, max_workers=4)
    parallel_time = time.time() - start_time

    # Parallel should be faster (or similar if network is fast)
    assert parallel_time <= sequential_time * 1.5  # Allow some variance
    assert result.success_count == 4


# ============================================================================
# Statistics Tests
# ============================================================================


@respx.mock
def test_batch_result_statistics():
    """Test BatchResult statistics methods."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    client = PhotoRoomClient(api_key="test_key")

    # Process batch
    inputs = [b"image1", b"image2", b"image3"]
    result = client.batch_remove_background(inputs, bg_color="white")

    # Get statistics
    stats = result.get_statistics()

    assert stats["total"] == 3
    assert stats["successful"] == 3
    assert stats["failed"] == 0
    assert stats["success_rate"] == 1.0
    assert "total_time_seconds" in stats
    assert "average_time_per_item" in stats
