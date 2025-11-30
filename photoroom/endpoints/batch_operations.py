"""Batch processing operations for PhotoRoom API.

This module provides batch processing methods for background removal and image editing.
"""

import time
import asyncio
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from ..types import (
    BatchInput,
    BatchItemResult,
    BatchProgress,
    ProgressCallback,
    ImageResponse,
)
from ..batch import BatchResult
from ..exceptions import BatchError


def _process_batch_sync(
    self,
    inputs: List[BatchInput],
    operation: str,
    operation_kwargs: Optional[Dict[str, Any]] = None,
    max_workers: int = 5,
    on_error: str = "continue",
    progress_callback: Optional[ProgressCallback] = None,
    output_dir: Optional[str] = None,
    output_pattern: str = "{index}_{name}",
) -> BatchResult:
    """Process a batch of images synchronously using thread pool.

    Args:
        inputs: List of image inputs (file paths, Path objects, or bytes)
        operation: Operation name ("remove_background" or "edit_image")
        operation_kwargs: Additional kwargs to pass to the operation
        max_workers: Maximum number of concurrent workers (default: 5)
        on_error: Error handling strategy ("continue", "fail_fast", or "retry")
        progress_callback: Optional callback function called with BatchProgress
        output_dir: Optional directory to save results automatically
        output_pattern: Filename pattern for output files (supports {index}, {name})

    Returns:
        BatchResult containing all results

    Raises:
        BatchError: If on_error="fail_fast" and any item fails
    """
    operation_kwargs = operation_kwargs or {}
    results: List[BatchItemResult] = []
    results_lock = threading.Lock()

    # Initialize progress tracking
    progress = BatchProgress(total=len(inputs))
    start_time = time.time()

    def update_progress():
        """Update progress with timing estimates."""
        elapsed = time.time() - start_time
        progress.elapsed_seconds = elapsed

        # Estimate remaining time
        if progress.completed > 0:
            avg_time_per_item = elapsed / progress.completed
            remaining_items = progress.total - progress.completed
            progress.estimated_remaining_seconds = avg_time_per_item * remaining_items

        # Call progress callback if provided
        if progress_callback:
            progress_callback(progress)

    def process_single_item(index: int, input_data: BatchInput) -> BatchItemResult:
        """Process a single item."""
        try:
            # Determine input file name for metadata
            if isinstance(input_data, (str, Path)):
                input_file = str(input_data)
            else:
                input_file = f"bytes_input_{index}"

            # Get the operation method
            if operation == "remove_background":
                method = self.remove_background
            elif operation == "edit_image":
                method = self.edit_image
            else:
                raise ValueError(f"Unknown operation: {operation}")

            # Execute the operation
            result = method(input_data, **operation_kwargs)

            # Save to output directory if specified
            output_file = None
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                # Format filename
                original_name = Path(input_file).name if isinstance(input_data, (str, Path)) else f"image_{index}.png"
                filename = output_pattern.format(index=index, name=original_name)
                output_file = str(output_path / filename)

                # Save the result
                result.save(output_file)

            return BatchItemResult(
                index=index,
                input_file=input_file,
                success=True,
                result=result,
                output_file=output_file,
            )

        except Exception as e:
            # Handle error based on strategy
            if on_error == "fail_fast":
                raise BatchError(f"Batch processing failed at item {index}: {e}") from e

            return BatchItemResult(
                index=index,
                input_file=str(input_data) if isinstance(input_data, (str, Path)) else f"bytes_input_{index}",
                success=False,
                error=e,
            )

    # Process items using thread pool
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(process_single_item, i, input_data): i
            for i, input_data in enumerate(inputs)
        }

        # Process completed tasks
        for future in as_completed(future_to_index):
            result = future.result()

            # Update results list
            with results_lock:
                results.append(result)

                # Update progress
                progress.completed += 1
                if result.success:
                    progress.successful += 1
                else:
                    progress.failed += 1

                update_progress()

    # Sort results by index to maintain order
    results.sort(key=lambda x: x.index)

    # Calculate total time
    total_time = time.time() - start_time

    return BatchResult(results=results, total_time=total_time, progress=progress)


def batch_remove_background(
    self,
    inputs: List[BatchInput],
    # Background removal options
    bg_color: Optional[str] = None,
    format: str = "png",
    size: Optional[str] = None,
    # Batch processing options
    max_workers: int = 5,
    on_error: str = "continue",
    progress_callback: Optional[ProgressCallback] = None,
    output_dir: Optional[str] = None,
    output_pattern: str = "{index}_{name}",
    **kwargs: Any,
) -> BatchResult:
    """Process multiple images for background removal.

    Args:
        inputs: List of image inputs (file paths, Path objects, or bytes)
        bg_color: Background color (e.g., "white", "#FF0000")
        format: Output format ("png", "jpg", "webp")
        size: Output size specification
        max_workers: Maximum concurrent workers (default: 5)
        on_error: Error strategy ("continue", "fail_fast")
        progress_callback: Optional callback for progress updates
        output_dir: Optional directory to auto-save results
        output_pattern: Filename pattern (supports {index}, {name})
        **kwargs: Additional parameters for remove_background

    Returns:
        BatchResult with all processing results

    Example:
        >>> client = PhotoRoomClient(api_key="...", rate_limit=10.0)
        >>> inputs = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
        >>> result = client.batch_remove_background(
        ...     inputs,
        ...     bg_color="white",
        ...     max_workers=3,
        ...     output_dir="output/"
        ... )
        >>> print(f"Processed {result.success_count}/{result.total} images")
    """
    # Build operation kwargs
    operation_kwargs = {
        "bg_color": bg_color,
        "format": format,
        "size": size,
        **kwargs,
    }
    # Remove None values
    operation_kwargs = {k: v for k, v in operation_kwargs.items() if v is not None}

    return _process_batch_sync(
        self,
        inputs=inputs,
        operation="remove_background",
        operation_kwargs=operation_kwargs,
        max_workers=max_workers,
        on_error=on_error,
        progress_callback=progress_callback,
        output_dir=output_dir,
        output_pattern=output_pattern,
    )


def batch_edit_image(
    self,
    inputs: List[BatchInput],
    # Background options
    background_color: Optional[str] = None,
    background_prompt: Optional[str] = None,
    background_seed: Optional[int] = None,
    # Image options
    remove_background: bool = True,
    output_size: Optional[str] = None,
    padding: Optional[str] = None,
    export_format: str = "png",
    # Batch processing options
    max_workers: int = 5,
    on_error: str = "continue",
    progress_callback: Optional[ProgressCallback] = None,
    output_dir: Optional[str] = None,
    output_pattern: str = "{index}_{name}",
    **kwargs: Any,
) -> BatchResult:
    """Process multiple images with editing operations.

    Args:
        inputs: List of image inputs (file paths, Path objects, or bytes)
        background_color: Background color
        background_prompt: AI background generation prompt
        background_seed: Seed for reproducible backgrounds
        remove_background: Whether to remove background
        output_size: Output size specification
        padding: Padding around subject
        export_format: Output format ("png", "jpg", "webp")
        max_workers: Maximum concurrent workers (default: 5)
        on_error: Error strategy ("continue", "fail_fast")
        progress_callback: Optional callback for progress updates
        output_dir: Optional directory to auto-save results
        output_pattern: Filename pattern (supports {index}, {name})
        **kwargs: Additional parameters for edit_image

    Returns:
        BatchResult with all processing results

    Example:
        >>> client = PhotoRoomClient(api_key="...", rate_limit=10.0)
        >>> inputs = ["photo1.jpg", "photo2.jpg"]
        >>> result = client.batch_edit_image(
        ...     inputs,
        ...     background_prompt="on a beach",
        ...     max_workers=2,
        ...     output_dir="edited/"
        ... )
        >>> result.raise_on_failure()  # Raise if any failed
    """
    # Build operation kwargs
    operation_kwargs = {
        "background_color": background_color,
        "background_prompt": background_prompt,
        "background_seed": background_seed,
        "remove_background": remove_background,
        "output_size": output_size,
        "padding": padding,
        "export_format": export_format,
        **kwargs,
    }
    # Remove None values
    operation_kwargs = {k: v for k, v in operation_kwargs.items() if v is not None}

    return _process_batch_sync(
        self,
        inputs=inputs,
        operation="edit_image",
        operation_kwargs=operation_kwargs,
        max_workers=max_workers,
        on_error=on_error,
        progress_callback=progress_callback,
        output_dir=output_dir,
        output_pattern=output_pattern,
    )


# ============================================================================
# Async Batch Processing
# ============================================================================


async def _process_batch_async(
    self,
    inputs: List[BatchInput],
    operation: str,
    operation_kwargs: Optional[Dict[str, Any]] = None,
    max_concurrency: int = 5,
    on_error: str = "continue",
    progress_callback: Optional[ProgressCallback] = None,
    output_dir: Optional[str] = None,
    output_pattern: str = "{index}_{name}",
) -> BatchResult:
    """Process a batch of images asynchronously.

    Args:
        inputs: List of image inputs (file paths, Path objects, or bytes)
        operation: Operation name ("remove_background" or "edit_image")
        operation_kwargs: Additional kwargs to pass to the operation
        max_concurrency: Maximum number of concurrent operations (default: 5)
        on_error: Error handling strategy ("continue", "fail_fast", or "retry")
        progress_callback: Optional callback function called with BatchProgress
        output_dir: Optional directory to save results automatically
        output_pattern: Filename pattern for output files (supports {index}, {name})

    Returns:
        BatchResult containing all results

    Raises:
        BatchError: If on_error="fail_fast" and any item fails
    """
    operation_kwargs = operation_kwargs or {}
    results: List[BatchItemResult] = []
    results_lock = asyncio.Lock()

    # Initialize progress tracking
    progress = BatchProgress(total=len(inputs))
    start_time = time.time()

    async def update_progress():
        """Update progress with timing estimates."""
        elapsed = time.time() - start_time
        progress.elapsed_seconds = elapsed

        # Estimate remaining time
        if progress.completed > 0:
            avg_time_per_item = elapsed / progress.completed
            remaining_items = progress.total - progress.completed
            progress.estimated_remaining_seconds = avg_time_per_item * remaining_items

        # Call progress callback if provided
        if progress_callback:
            # Handle both sync and async callbacks
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(progress)
            else:
                progress_callback(progress)

    async def process_single_item(index: int, input_data: BatchInput) -> BatchItemResult:
        """Process a single item asynchronously."""
        try:
            # Determine input file name for metadata
            if isinstance(input_data, (str, Path)):
                input_file = str(input_data)
            else:
                input_file = f"bytes_input_{index}"

            # Get the async operation method
            if operation == "remove_background":
                method = self.aremove_background
            elif operation == "edit_image":
                method = self.aedit_image
            else:
                raise ValueError(f"Unknown operation: {operation}")

            # Execute the operation
            result = await method(input_data, **operation_kwargs)

            # Save to output directory if specified
            output_file = None
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                # Format filename
                original_name = Path(input_file).name if isinstance(input_data, (str, Path)) else f"image_{index}.png"
                filename = output_pattern.format(index=index, name=original_name)
                output_file = str(output_path / filename)

                # Save the result
                result.save(output_file)

            return BatchItemResult(
                index=index,
                input_file=input_file,
                success=True,
                result=result,
                output_file=output_file,
            )

        except Exception as e:
            # Handle error based on strategy
            if on_error == "fail_fast":
                raise BatchError(f"Batch processing failed at item {index}: {e}") from e

            return BatchItemResult(
                index=index,
                input_file=str(input_data) if isinstance(input_data, (str, Path)) else f"bytes_input_{index}",
                success=False,
                error=e,
            )

    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrency)

    async def process_with_semaphore(index: int, input_data: BatchInput):
        """Process item with semaphore for concurrency control."""
        async with semaphore:
            result = await process_single_item(index, input_data)

            # Update results list
            async with results_lock:
                results.append(result)

                # Update progress
                progress.completed += 1
                if result.success:
                    progress.successful += 1
                else:
                    progress.failed += 1

                await update_progress()

            return result

    # Process all items concurrently (with semaphore limiting concurrency)
    tasks = [
        process_with_semaphore(i, input_data)
        for i, input_data in enumerate(inputs)
    ]
    await asyncio.gather(*tasks)

    # Sort results by index to maintain order
    results.sort(key=lambda x: x.index)

    # Calculate total time
    total_time = time.time() - start_time

    return BatchResult(results=results, total_time=total_time, progress=progress)


async def abatch_remove_background(
    self,
    inputs: List[BatchInput],
    # Background removal options
    bg_color: Optional[str] = None,
    format: str = "png",
    size: Optional[str] = None,
    # Batch processing options
    max_concurrency: int = 5,
    on_error: str = "continue",
    progress_callback: Optional[ProgressCallback] = None,
    output_dir: Optional[str] = None,
    output_pattern: str = "{index}_{name}",
    **kwargs: Any,
) -> BatchResult:
    """Process multiple images for background removal asynchronously.

    Args:
        inputs: List of image inputs (file paths, Path objects, or bytes)
        bg_color: Background color (e.g., "white", "#FF0000")
        format: Output format ("png", "jpg", "webp")
        size: Output size specification
        max_concurrency: Maximum concurrent operations (default: 5)
        on_error: Error strategy ("continue", "fail_fast")
        progress_callback: Optional callback for progress updates
        output_dir: Optional directory to auto-save results
        output_pattern: Filename pattern (supports {index}, {name})
        **kwargs: Additional parameters for remove_background

    Returns:
        BatchResult with all processing results

    Example:
        >>> async with PhotoRoomClient(async_mode=True) as client:
        ...     inputs = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
        ...     result = await client.abatch_remove_background(
        ...         inputs,
        ...         bg_color="white",
        ...         max_concurrency=3,
        ...         output_dir="output/"
        ...     )
        ...     print(f"Processed {result.success_count}/{result.total} images")
    """
    # Build operation kwargs
    operation_kwargs = {
        "bg_color": bg_color,
        "format": format,
        "size": size,
        **kwargs,
    }
    # Remove None values
    operation_kwargs = {k: v for k, v in operation_kwargs.items() if v is not None}

    return await _process_batch_async(
        self,
        inputs=inputs,
        operation="remove_background",
        operation_kwargs=operation_kwargs,
        max_concurrency=max_concurrency,
        on_error=on_error,
        progress_callback=progress_callback,
        output_dir=output_dir,
        output_pattern=output_pattern,
    )


async def abatch_edit_image(
    self,
    inputs: List[BatchInput],
    # Background options
    background_color: Optional[str] = None,
    background_prompt: Optional[str] = None,
    background_seed: Optional[int] = None,
    # Image options
    remove_background: bool = True,
    output_size: Optional[str] = None,
    padding: Optional[str] = None,
    export_format: str = "png",
    # Batch processing options
    max_concurrency: int = 5,
    on_error: str = "continue",
    progress_callback: Optional[ProgressCallback] = None,
    output_dir: Optional[str] = None,
    output_pattern: str = "{index}_{name}",
    **kwargs: Any,
) -> BatchResult:
    """Process multiple images with editing operations asynchronously.

    Args:
        inputs: List of image inputs (file paths, Path objects, or bytes)
        background_color: Background color
        background_prompt: AI background generation prompt
        background_seed: Seed for reproducible backgrounds
        remove_background: Whether to remove background
        output_size: Output size specification
        padding: Padding around subject
        export_format: Output format ("png", "jpg", "webp")
        max_concurrency: Maximum concurrent operations (default: 5)
        on_error: Error strategy ("continue", "fail_fast")
        progress_callback: Optional callback for progress updates
        output_dir: Optional directory to auto-save results
        output_pattern: Filename pattern (supports {index}, {name})
        **kwargs: Additional parameters for edit_image

    Returns:
        BatchResult with all processing results

    Example:
        >>> async with PhotoRoomClient(async_mode=True) as client:
        ...     inputs = ["photo1.jpg", "photo2.jpg"]
        ...     result = await client.abatch_edit_image(
        ...         inputs,
        ...         background_prompt="on a beach",
        ...         max_concurrency=2,
        ...         output_dir="edited/"
        ...     )
        ...     result.raise_on_failure()  # Raise if any failed
    """
    # Build operation kwargs
    operation_kwargs = {
        "background_color": background_color,
        "background_prompt": background_prompt,
        "background_seed": background_seed,
        "remove_background": remove_background,
        "output_size": output_size,
        "padding": padding,
        "export_format": export_format,
        **kwargs,
    }
    # Remove None values
    operation_kwargs = {k: v for k, v in operation_kwargs.items() if v is not None}

    return await _process_batch_async(
        self,
        inputs=inputs,
        operation="edit_image",
        operation_kwargs=operation_kwargs,
        max_concurrency=max_concurrency,
        on_error=on_error,
        progress_callback=progress_callback,
        output_dir=output_dir,
        output_pattern=output_pattern,
    )
