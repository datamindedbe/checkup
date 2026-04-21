"""Metric and Measurement classes."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field

from checkup.types import Context

if TYPE_CHECKING:
    from checkup.provider import Provider


class ExecutorType(Enum):
    """
    Executor types for metric calculation.

    Metrics can specify which executor to use for their calculation:
    - THREAD: ThreadPoolExecutor (default) - best for I/O-bound operations
    - PROCESS: ProcessPoolExecutor - best for CPU-bound operations
    - ASYNCIO: asyncio event loop - best for async I/O operations
    """

    THREAD = "thread"
    PROCESS = "process"
    ASYNCIO = "asyncio"


class Metric(ABC, BaseModel):
    """
    Base class for all metrics.

    Metrics are immutable Pydantic models that define how to calculate values.
    The calculate() method returns a Measurement with the result.
    """

    name: ClassVar[str]
    description: ClassVar[str]
    unit: ClassVar[str]
    executor: ClassVar[ExecutorType] = ExecutorType.THREAD

    model_config = {"frozen": True}  # Make instances immutable

    @abstractmethod
    def calculate(
        self, context: Context, measurements: dict[type["Metric"], "Measurement"]
    ) -> "Measurement":
        """
        Calculate metric and return a Measurement.

        Args:
            context: General context enriched by providers
            measurements: Dict mapping Metric classes to their Measurements (dependencies)

        Returns:
            Measurement with the calculated value
        """
        pass

    def measure(
        self,
        value: Any = None,
        tags: dict | None = None,
        diagnostic: str = "",
    ) -> "Measurement":
        """
        Create a Measurement for this metric.

        Helper method to create a Measurement with this metric's metadata.

        Args:
            value: The calculated value
            tags: Optional tags dict (will be merged with provider tags)
            diagnostic: Optional diagnostic message

        Returns:
            Measurement instance
        """
        return Measurement(
            metric=self,
            value=value,
            tags=tags or {},
            diagnostic=diagnostic,
        )

    @classmethod
    def depends_on(cls) -> list[type["Metric"]]:
        """
        Return list of metric classes this metric depends on.

        Returns:
            List of metric classes (empty by default)
        """
        return []

    @classmethod
    def providers(cls) -> list[type["Provider"]]:
        """
        Return list of provider classes to enrich context.

        Returns:
            List of provider classes (empty by default)
        """
        return []


class Measurement(BaseModel):
    """
    Result of a metric calculation.

    Holds the metric that produced it, the calculated value, tags, and diagnostic information.
    """

    metric: Metric
    value: Any = None
    tags: dict = Field(default_factory=dict)
    diagnostic: str = ""
