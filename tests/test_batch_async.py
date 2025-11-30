"""Unit tests for asynchronous batch processing operations."""

import pytest
import time
import tempfile
import shutil
from pathlib import Path

import respx
import httpx

from photoroom import PhotoRoomClient, BatchResult, BatchProgress
from photoroom.exceptions import BatchError


# ============================================================================
# Async Batch Remove Background Tests
# ============================================================================


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_remove_background_all_successful():
    """Test async batch background removal with all successful items."""
    # Mock successful responses
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    async with PhotoRoomClient(api_key="test_key", async_mode=True) as client:
        # Process batch
        inputs = [b"image1", b"image2", b"image3"]
        result = await client.abatch_remove_background(
            inputs, bg_color="white", max_concurrency=2
        )

        assert isinstance(result, BatchResult)
        assert result.total == 3
        assert result.success_count == 3
        assert result.failure_count == 0
        assert result.all_successful is True


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_remove_background_with_failures():
    """Test async batch background removal with some failures."""
    # Mock responses: first succeeds, second fails, third succeeds
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        side_effect=[
            httpx.Response(200, content=b"fake_image_data_1"),
            httpx.Response(400, json={"detail": "Bad request"}),
            httpx.Response(200, content=b"fake_image_data_3"),
        ]
    )

    async with PhotoRoomClient(
        api_key="test_key", async_mode=True, max_retries=0
    ) as client:
        # Process batch with continue on error
        inputs = [b"image1", b"image2", b"image3"]
        result = await client.abatch_remove_background(
            inputs, bg_color="white", max_concurrency=1, on_error="continue"
        )

        assert result.total == 3
        assert result.success_count == 2
        assert result.failure_count == 1
        assert result.any_failed is True


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_remove_background_fail_fast():
    """Test async batch with fail_fast error strategy."""
    # Mock first request to fail
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(400, json={"detail": "Bad request"})
    )

    async with PhotoRoomClient(
        api_key="test_key", async_mode=True, max_retries=0
    ) as client:
        # Process batch with fail_fast
        inputs = [b"image1", b"image2", b"image3"]

        with pytest.raises(BatchError, match="Batch processing failed"):
            await client.abatch_remove_background(
                inputs, bg_color="white", max_concurrency=1, on_error="fail_fast"
            )


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_remove_background_with_output_dir():
    """Test async batch processing with automatic output saving."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"processed_image_data")
    )

    # Create temporary output directory
    temp_dir = tempfile.mkdtemp()

    try:
        async with PhotoRoomClient(api_key="test_key", async_mode=True) as client:
            # Process batch with output directory
            inputs = [b"image1", b"image2"]
            output_dir = Path(temp_dir) / "output"

            result = await client.abatch_remove_background(
                inputs,
                bg_color="white",
                max_concurrency=2,
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
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_remove_background_with_progress_callback():
    """Test async batch processing with progress callback."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    async with PhotoRoomClient(api_key="test_key", async_mode=True) as client:
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
        result = await client.abatch_remove_background(
            inputs, bg_color="white", max_concurrency=1, progress_callback=progress_callback
        )

        assert result.success_count == 3

        # Verify progress updates were called
        assert len(progress_updates) == 3
        assert progress_updates[-1]["completed"] == 3
        assert progress_updates[-1]["percent"] == 100.0


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_remove_background_empty_input():
    """Test async batch processing with empty input list."""
    async with PhotoRoomClient(api_key="test_key", async_mode=True) as client:
        result = await client.abatch_remove_background([], bg_color="white")

        assert result.total == 0
        assert result.success_count == 0
        assert result.failure_count == 0


# ============================================================================
# Async Batch Edit Image Tests
# ============================================================================


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_edit_image_all_successful():
    """Test async batch image editing with all successful items."""
    # Mock successful responses
    respx.post("https://image-api.photoroom.com/v2/edit").mock(
        return_value=httpx.Response(200, content=b"fake_edited_image")
    )

    async with PhotoRoomClient(api_key="test_key", async_mode=True) as client:
        # Process batch
        inputs = [b"image1", b"image2"]
        result = await client.abatch_edit_image(
            inputs, background_color="white", max_concurrency=2
        )

        assert isinstance(result, BatchResult)
        assert result.total == 2
        assert result.success_count == 2
        assert result.failure_count == 0


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_edit_image_with_background_prompt():
    """Test async batch editing with AI background prompt."""
    # Mock successful response
    respx.post("https://image-api.photoroom.com/v2/edit").mock(
        return_value=httpx.Response(200, content=b"fake_edited_image")
    )

    async with PhotoRoomClient(api_key="test_key", async_mode=True) as client:
        # Process batch with background prompt
        inputs = [b"image1", b"image2"]
        result = await client.abatch_edit_image(
            inputs,
            background_prompt="on a beach at sunset",
            background_seed=42,
            max_concurrency=2,
        )

        assert result.success_count == 2


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_edit_image_with_failures():
    """Test async batch editing with some failures."""
    # Mock responses: alternating success/failure
    respx.post("https://image-api.photoroom.com/v2/edit").mock(
        side_effect=[
            httpx.Response(200, content=b"fake_edited_image_1"),
            httpx.Response(500, json={"error": {"message": "Server error"}}),
            httpx.Response(200, content=b"fake_edited_image_3"),
            httpx.Response(500, json={"error": {"message": "Server error"}}),
        ]
    )

    async with PhotoRoomClient(
        api_key="test_key", async_mode=True, max_retries=0
    ) as client:
        # Process batch
        inputs = [b"image1", b"image2", b"image3", b"image4"]
        result = await client.abatch_edit_image(
            inputs, background_color="white", max_concurrency=1, on_error="continue"
        )

        assert result.total == 4
        assert result.success_count == 2
        assert result.failure_count == 2


# ============================================================================
# Integration with Rate Limiting
# ============================================================================


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_with_rate_limiting():
    """Test that async batch operations respect rate limiting."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    # Create client with rate limiting (2 req/sec)
    async with PhotoRoomClient(
        api_key="test_key",
        async_mode=True,
        rate_limit=2.0,
        rate_limit_strategy="wait",
    ) as client:
        # Process batch - should respect rate limit
        start_time = time.time()
        inputs = [b"image1", b"image2", b"image3"]
        result = await client.abatch_remove_background(
            inputs, bg_color="white", max_concurrency=1  # Sequential to test rate limiting
        )
        elapsed = time.time() - start_time

        assert result.success_count == 3

        # With 2 req/sec and burst_size=2:
        # First 2 requests instant, 3rd waits ~0.5s
        assert elapsed >= 0.4  # Allow some timing variance


# ============================================================================
# Concurrency Tests
# ============================================================================


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_concurrency_control():
    """Test that async batch processing respects max_concurrency."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    async with PhotoRoomClient(api_key="test_key", async_mode=True) as client:
        # Process batch with concurrency limit
        inputs = [b"image1", b"image2", b"image3", b"image4", b"image5"]
        result = await client.abatch_remove_background(
            inputs, bg_color="white", max_concurrency=2
        )

        assert result.success_count == 5


# ============================================================================
# Async Progress Callback Test
# ============================================================================


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_with_async_progress_callback():
    """Test async batch processing with async progress callback."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    async with PhotoRoomClient(api_key="test_key", async_mode=True) as client:
        # Track progress updates
        progress_updates = []

        async def async_progress_callback(progress: BatchProgress):
            """Async progress callback for testing."""
            progress_updates.append(progress.completed)

        # Process batch
        inputs = [b"image1", b"image2", b"image3"]
        result = await client.abatch_remove_background(
            inputs,
            bg_color="white",
            max_concurrency=1,
            progress_callback=async_progress_callback,
        )

        assert result.success_count == 3
        assert len(progress_updates) == 3
        assert progress_updates == [1, 2, 3]


# ============================================================================
# File Input Tests
# ============================================================================


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_with_file_paths():
    """Test async batch processing with file path inputs."""
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

        async with PhotoRoomClient(api_key="test_key", async_mode=True) as client:
            # Process batch with file paths
            inputs = [str(image1), str(image2)]
            result = await client.abatch_remove_background(inputs, bg_color="white")

            assert result.success_count == 2
            assert result.results[0].input_file == str(image1)
            assert result.results[1].input_file == str(image2)

    finally:
        shutil.rmtree(temp_dir)


# ============================================================================
# Error Handling Tests
# ============================================================================


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_result_raise_on_failure():
    """Test async BatchResult.raise_on_failure() method."""
    # Mock responses: one failure
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        side_effect=[
            httpx.Response(200, content=b"fake_image_data_1"),
            httpx.Response(400, json={"detail": "Bad request"}),
            httpx.Response(200, content=b"fake_image_data_3"),
        ]
    )

    async with PhotoRoomClient(
        api_key="test_key", async_mode=True, max_retries=0
    ) as client:
        # Process batch
        inputs = [b"image1", b"image2", b"image3"]
        result = await client.abatch_remove_background(
            inputs, bg_color="white", max_concurrency=1, on_error="continue"
        )

        assert result.any_failed is True

        # Should raise exception
        from photoroom.exceptions import BatchPartialFailureError

        with pytest.raises(BatchPartialFailureError) as exc_info:
            result.raise_on_failure()

        assert exc_info.value.successful_count == 2
        assert exc_info.value.failed_count == 1


# ============================================================================
# Statistics Tests
# ============================================================================


@respx.mock
@pytest.mark.anyio(backends=["asyncio"])
async def test_async_batch_result_statistics():
    """Test async BatchResult statistics methods."""
    # Mock successful response
    respx.post("https://sdk.photoroom.com/v1/segment").mock(
        return_value=httpx.Response(200, content=b"fake_image_data")
    )

    async with PhotoRoomClient(api_key="test_key", async_mode=True) as client:
        # Process batch
        inputs = [b"image1", b"image2", b"image3"]
        result = await client.abatch_remove_background(inputs, bg_color="white")

        # Get statistics
        stats = result.get_statistics()

        assert stats["total"] == 3
        assert stats["successful"] == 3
        assert stats["failed"] == 0
        assert stats["success_rate"] == 1.0
        assert "total_time_seconds" in stats
        assert "average_time_per_item" in stats
