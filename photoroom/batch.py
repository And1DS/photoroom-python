"""Batch Processing Infrastructure for PhotoRoom API.

This module provides classes and utilities for batch processing operations.
"""

import time
from typing import List, Optional
from pathlib import Path

from .types import BatchItemResult, BatchProgress
from .exceptions import BatchPartialFailureError


class BatchResult:
    """Result container for batch processing operations.

    Provides comprehensive access to batch processing results, including
    successes, failures, statistics, and filtering methods.

    Attributes:
        results: List of all BatchItemResult objects
        total_time: Total processing time in seconds
        progress: Final BatchProgress snapshot
    """

    def __init__(
        self,
        results: List[BatchItemResult],
        total_time: float,
        progress: Optional[BatchProgress] = None,
    ):
        """Initialize BatchResult.

        Args:
            results: List of BatchItemResult objects
            total_time: Total processing time in seconds
            progress: Optional BatchProgress snapshot
        """
        self.results = results
        self.total_time = total_time
        self._progress = progress

    @property
    def total(self) -> int:
        """Get total number of items processed.

        Returns:
            Total number of items
        """
        return len(self.results)

    @property
    def successful(self) -> List[BatchItemResult]:
        """Get list of successful results.

        Returns:
            List of BatchItemResult objects where success=True
        """
        return [r for r in self.results if r.success]

    @property
    def failed(self) -> List[BatchItemResult]:
        """Get list of failed results.

        Returns:
            List of BatchItemResult objects where success=False
        """
        return [r for r in self.results if not r.success]

    @property
    def success_count(self) -> int:
        """Get count of successful items.

        Returns:
            Number of successful items
        """
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        """Get count of failed items.

        Returns:
            Number of failed items
        """
        return len(self.failed)

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0-1).

        Returns:
            Success rate as decimal (0-1)
        """
        if self.total == 0:
            return 0.0
        return self.success_count / self.total

    @property
    def all_successful(self) -> bool:
        """Check if all items succeeded.

        Returns:
            True if all items succeeded, False otherwise
        """
        return self.failure_count == 0

    @property
    def any_failed(self) -> bool:
        """Check if any items failed.

        Returns:
            True if any items failed, False otherwise
        """
        return self.failure_count > 0

    @property
    def progress(self) -> BatchProgress:
        """Get progress information.

        Returns:
            BatchProgress object with final statistics
        """
        if self._progress is not None:
            return self._progress

        # Create progress from results if not provided
        return BatchProgress(
            total=self.total,
            completed=self.total,
            successful=self.success_count,
            failed=self.failure_count,
            elapsed_seconds=self.total_time,
            estimated_remaining_seconds=0.0,
        )

    def raise_on_failure(self) -> None:
        """Raise exception if any items failed.

        Raises:
            BatchPartialFailureError: If any items failed
        """
        if self.any_failed:
            failures = [(r.index, r.error) for r in self.failed]
            raise BatchPartialFailureError(
                message=f"Batch processing completed with {self.failure_count} failures",
                successful_count=self.success_count,
                failed_count=self.failure_count,
                failures=failures,
            )

    def get_result(self, index: int) -> Optional[BatchItemResult]:
        """Get result by index.

        Args:
            index: Index of the item in original batch

        Returns:
            BatchItemResult if found, None otherwise
        """
        for result in self.results:
            if result.index == index:
                return result
        return None

    def save_successful(self, output_dir: str, pattern: str = "{index}_{name}") -> int:
        """Save all successful results to a directory.

        Args:
            output_dir: Directory to save results
            pattern: Filename pattern. Supports {index} and {name} placeholders.
                    Default: "{index}_{name}"

        Returns:
            Number of files saved

        Example:
            >>> result.save_successful("output/", pattern="{index}_result.png")
            >>> result.save_successful("output/", pattern="processed_{name}")
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_count = 0
        for item in self.successful:
            if item.result is None:
                continue

            # Extract original filename if available
            original_name = Path(item.input_file).name if item.input_file else "image.png"

            # Format filename using pattern
            filename = pattern.format(index=item.index, name=original_name)
            file_path = output_path / filename

            # Save the image
            item.result.save(str(file_path))
            saved_count += 1

        return saved_count

    def get_statistics(self) -> dict:
        """Get detailed statistics about the batch.

        Returns:
            Dictionary with statistics
        """
        return {
            "total": self.total,
            "successful": self.success_count,
            "failed": self.failure_count,
            "success_rate": self.success_rate,
            "total_time_seconds": self.total_time,
            "average_time_per_item": self.total_time / self.total if self.total > 0 else 0,
        }

    def __repr__(self) -> str:
        """String representation of BatchResult."""
        return (
            f"BatchResult(total={self.total}, "
            f"successful={self.success_count}, "
            f"failed={self.failure_count}, "
            f"time={self.total_time:.2f}s)"
        )

    def __iter__(self):
        """Iterate over all results."""
        return iter(self.results)

    def __len__(self) -> int:
        """Get total number of results."""
        return len(self.results)

    def __getitem__(self, index: int) -> BatchItemResult:
        """Get result by index using bracket notation.

        Args:
            index: Index of the result

        Returns:
            BatchItemResult at the given index
        """
        return self.results[index]
