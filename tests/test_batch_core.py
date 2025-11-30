"""Unit tests for batch processing core infrastructure."""

import pytest
from pathlib import Path
import tempfile
import shutil

from photoroom.types import BatchItemResult, BatchProgress, ImageResponse
from photoroom.batch import BatchResult
from photoroom.exceptions import BatchPartialFailureError


# ============================================================================
# BatchProgress Tests
# ============================================================================


def test_batch_progress_initial_state():
    """Test BatchProgress initial state."""
    progress = BatchProgress(total=10)

    assert progress.total == 10
    assert progress.completed == 0
    assert progress.successful == 0
    assert progress.failed == 0
    assert progress.elapsed_seconds == 0.0
    assert progress.estimated_remaining_seconds is None


def test_batch_progress_percentage():
    """Test progress percentage calculation."""
    progress = BatchProgress(total=10, completed=5)
    assert progress.progress_percent == 50.0

    progress = BatchProgress(total=10, completed=10)
    assert progress.progress_percent == 100.0

    progress = BatchProgress(total=0, completed=0)
    assert progress.progress_percent == 100.0  # Edge case: empty batch


def test_batch_progress_is_complete():
    """Test is_complete property."""
    progress = BatchProgress(total=10, completed=5)
    assert not progress.is_complete

    progress = BatchProgress(total=10, completed=10)
    assert progress.is_complete

    progress = BatchProgress(total=10, completed=15)  # Over-complete
    assert progress.is_complete


def test_batch_progress_success_rate():
    """Test success rate calculation."""
    progress = BatchProgress(total=10, completed=10, successful=8, failed=2)
    assert progress.success_rate == 0.8

    progress = BatchProgress(total=10, completed=10, successful=10, failed=0)
    assert progress.success_rate == 1.0

    progress = BatchProgress(total=10, completed=0, successful=0, failed=0)
    assert progress.success_rate == 0.0


def test_batch_progress_repr():
    """Test BatchProgress string representation."""
    progress = BatchProgress(total=10, completed=5, successful=4, failed=1)
    repr_str = repr(progress)

    assert "5/10" in repr_str
    assert "50.0%" in repr_str
    assert "success=4" in repr_str
    assert "failed=1" in repr_str


# ============================================================================
# BatchItemResult Tests
# ============================================================================


def test_batch_item_result_success():
    """Test successful BatchItemResult."""
    image_response = ImageResponse(image_data=b"fake_image", metadata={})
    result = BatchItemResult(
        index=0,
        input_file="input.jpg",
        success=True,
        result=image_response,
        output_file="output.png",
    )

    assert result.index == 0
    assert result.input_file == "input.jpg"
    assert result.success is True
    assert result.result == image_response
    assert result.error is None
    assert result.output_file == "output.png"


def test_batch_item_result_failure():
    """Test failed BatchItemResult."""
    error = ValueError("Test error")
    result = BatchItemResult(
        index=1, input_file="input2.jpg", success=False, error=error
    )

    assert result.index == 1
    assert result.input_file == "input2.jpg"
    assert result.success is False
    assert result.result is None
    assert result.error == error
    assert result.output_file is None


def test_batch_item_result_repr():
    """Test BatchItemResult string representation."""
    # Success case
    image_response = ImageResponse(image_data=b"x" * 1024, metadata={})
    result = BatchItemResult(
        index=0, input_file="input.jpg", success=True, result=image_response
    )
    repr_str = repr(result)
    assert "success=True" in repr_str
    assert "1.0KB" in repr_str

    # Failure case
    result = BatchItemResult(
        index=1,
        input_file="input2.jpg",
        success=False,
        error=ValueError("Test error message"),
    )
    repr_str = repr(result)
    assert "success=False" in repr_str
    assert "Test error" in repr_str


# ============================================================================
# BatchResult Tests
# ============================================================================


def test_batch_result_all_successful():
    """Test BatchResult with all successful items."""
    results = [
        BatchItemResult(
            index=i,
            input_file=f"input{i}.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        )
        for i in range(5)
    ]

    batch_result = BatchResult(results=results, total_time=10.0)

    assert batch_result.total == 5
    assert batch_result.success_count == 5
    assert batch_result.failure_count == 0
    assert batch_result.success_rate == 1.0
    assert batch_result.all_successful is True
    assert batch_result.any_failed is False


def test_batch_result_partial_failures():
    """Test BatchResult with some failures."""
    results = [
        BatchItemResult(
            index=0,
            input_file="input0.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        ),
        BatchItemResult(
            index=1, input_file="input1.jpg", success=False, error=ValueError("Error 1")
        ),
        BatchItemResult(
            index=2,
            input_file="input2.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        ),
        BatchItemResult(
            index=3, input_file="input3.jpg", success=False, error=ValueError("Error 3")
        ),
    ]

    batch_result = BatchResult(results=results, total_time=10.0)

    assert batch_result.total == 4
    assert batch_result.success_count == 2
    assert batch_result.failure_count == 2
    assert batch_result.success_rate == 0.5
    assert batch_result.all_successful is False
    assert batch_result.any_failed is True


def test_batch_result_successful_and_failed_filters():
    """Test successful and failed property filters."""
    results = [
        BatchItemResult(
            index=0,
            input_file="input0.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        ),
        BatchItemResult(
            index=1, input_file="input1.jpg", success=False, error=ValueError("Error")
        ),
        BatchItemResult(
            index=2,
            input_file="input2.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        ),
    ]

    batch_result = BatchResult(results=results, total_time=10.0)

    successful = batch_result.successful
    assert len(successful) == 2
    assert all(r.success for r in successful)

    failed = batch_result.failed
    assert len(failed) == 1
    assert all(not r.success for r in failed)


def test_batch_result_raise_on_failure():
    """Test raise_on_failure method."""
    # All successful - should not raise
    results = [
        BatchItemResult(
            index=0,
            input_file="input0.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        )
    ]
    batch_result = BatchResult(results=results, total_time=10.0)
    batch_result.raise_on_failure()  # Should not raise

    # With failures - should raise
    results = [
        BatchItemResult(
            index=0,
            input_file="input0.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        ),
        BatchItemResult(
            index=1, input_file="input1.jpg", success=False, error=ValueError("Error")
        ),
    ]
    batch_result = BatchResult(results=results, total_time=10.0)

    with pytest.raises(BatchPartialFailureError) as exc_info:
        batch_result.raise_on_failure()

    assert exc_info.value.successful_count == 1
    assert exc_info.value.failed_count == 1
    assert len(exc_info.value.failures) == 1


def test_batch_result_get_result():
    """Test get_result method."""
    results = [
        BatchItemResult(
            index=0,
            input_file="input0.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        ),
        BatchItemResult(
            index=5,
            input_file="input5.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        ),
    ]

    batch_result = BatchResult(results=results, total_time=10.0)

    # Existing result
    result = batch_result.get_result(0)
    assert result is not None
    assert result.index == 0

    result = batch_result.get_result(5)
    assert result is not None
    assert result.index == 5

    # Non-existing result
    result = batch_result.get_result(99)
    assert result is None


def test_batch_result_save_successful():
    """Test save_successful method."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        # Create results with some successful items
        results = [
            BatchItemResult(
                index=0,
                input_file="photo1.jpg",
                success=True,
                result=ImageResponse(image_data=b"image_data_1", metadata={}),
            ),
            BatchItemResult(
                index=1,
                input_file="photo2.jpg",
                success=False,
                error=ValueError("Error"),
            ),
            BatchItemResult(
                index=2,
                input_file="photo3.jpg",
                success=True,
                result=ImageResponse(image_data=b"image_data_2", metadata={}),
            ),
        ]

        batch_result = BatchResult(results=results, total_time=10.0)

        # Save with default pattern
        output_dir = Path(temp_dir) / "output"
        saved_count = batch_result.save_successful(
            str(output_dir), pattern="{index}_{name}"
        )

        assert saved_count == 2
        assert (output_dir / "0_photo1.jpg").exists()
        assert (output_dir / "2_photo3.jpg").exists()
        assert not (output_dir / "1_photo2.jpg").exists()  # Failed item not saved

        # Verify content
        content = (output_dir / "0_photo1.jpg").read_bytes()
        assert content == b"image_data_1"

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_batch_result_get_statistics():
    """Test get_statistics method."""
    results = [
        BatchItemResult(
            index=0,
            input_file="input0.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        ),
        BatchItemResult(
            index=1, input_file="input1.jpg", success=False, error=ValueError("Error")
        ),
        BatchItemResult(
            index=2,
            input_file="input2.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        ),
    ]

    batch_result = BatchResult(results=results, total_time=15.0)
    stats = batch_result.get_statistics()

    assert stats["total"] == 3
    assert stats["successful"] == 2
    assert stats["failed"] == 1
    assert stats["success_rate"] == pytest.approx(0.666, rel=1e-2)
    assert stats["total_time_seconds"] == 15.0
    assert stats["average_time_per_item"] == 5.0


def test_batch_result_progress_property():
    """Test progress property."""
    # Test with provided progress
    progress = BatchProgress(
        total=5,
        completed=5,
        successful=4,
        failed=1,
        elapsed_seconds=10.0,
        estimated_remaining_seconds=0.0,
    )
    results = [
        BatchItemResult(
            index=i,
            input_file=f"input{i}.jpg",
            success=i != 1,  # Index 1 fails
            result=ImageResponse(image_data=b"fake", metadata={}) if i != 1 else None,
            error=ValueError("Error") if i == 1 else None,
        )
        for i in range(5)
    ]
    batch_result = BatchResult(results=results, total_time=10.0, progress=progress)

    assert batch_result.progress == progress
    assert batch_result.progress.total == 5
    assert batch_result.progress.successful == 4

    # Test without provided progress (auto-generated)
    batch_result = BatchResult(results=results, total_time=10.0)
    progress = batch_result.progress

    assert progress.total == 5
    assert progress.completed == 5
    assert progress.successful == 4
    assert progress.failed == 1
    assert progress.elapsed_seconds == 10.0


def test_batch_result_iteration():
    """Test BatchResult iteration and indexing."""
    results = [
        BatchItemResult(
            index=i,
            input_file=f"input{i}.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        )
        for i in range(3)
    ]

    batch_result = BatchResult(results=results, total_time=10.0)

    # Test len()
    assert len(batch_result) == 3

    # Test iteration
    count = 0
    for result in batch_result:
        assert isinstance(result, BatchItemResult)
        count += 1
    assert count == 3

    # Test indexing
    assert batch_result[0].index == 0
    assert batch_result[1].index == 1
    assert batch_result[2].index == 2


def test_batch_result_repr():
    """Test BatchResult string representation."""
    results = [
        BatchItemResult(
            index=0,
            input_file="input0.jpg",
            success=True,
            result=ImageResponse(image_data=b"fake", metadata={}),
        ),
        BatchItemResult(
            index=1, input_file="input1.jpg", success=False, error=ValueError("Error")
        ),
    ]

    batch_result = BatchResult(results=results, total_time=12.34)
    repr_str = repr(batch_result)

    assert "total=2" in repr_str
    assert "successful=1" in repr_str
    assert "failed=1" in repr_str
    assert "12.34s" in repr_str


# ============================================================================
# Exception Tests
# ============================================================================


def test_batch_partial_failure_error():
    """Test BatchPartialFailureError exception."""
    failures = [(0, ValueError("Error 1")), (2, ValueError("Error 2"))]
    error = BatchPartialFailureError(
        message="Batch failed",
        successful_count=3,
        failed_count=2,
        failures=failures,
    )

    assert error.successful_count == 3
    assert error.failed_count == 2
    assert len(error.failures) == 2

    error_str = str(error)
    assert "3 succeeded" in error_str
    assert "2 failed" in error_str
