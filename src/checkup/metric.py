"""Metric and Measurement classes."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any

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

    Metrics are Pydantic models that define how to calculate values.
    The calculate() method returns a Measurement with the result.

    Subclasses should define name, description, unit as class-level defaults,
    but these can be overridden via constructor for custom instances.
    """

    name: str
    description: str = ""
    unit: str = ""

    model_config = {"frozen": True}

    @classmethod
    def get_executor(cls) -> ExecutorType:
        """
        Get the executor type for this metric class.
        """

        return getattr(cls, "executor", ExecutorType.THREAD)

    @abstractmethod
    def calculate(
        self,
        context: Context,
        measurements: dict[type["Metric"], list["Measurement"]],
    ) -> "Measurement":
        """
        Calculate metric and return a Measurement.

        Args:
            context: General context enriched by providers
            measurements: Dict mapping Metric classes to lists of their Measurements

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

    def get_single(
        self,
        measurements: dict[type["Metric"], list["Measurement"]],
        metric_cls: type["Metric"],
    ) -> "Measurement":
        """
        Get a single measurement for a dependency, erroring if not exactly one.

        Convenience method for metrics that expect exactly one instance of a dependent metric.

        Args:
            measurements: The measurements dict passed to calculate()
            metric_cls: The metric class to look up

        Returns:
            The single Measurement

        Raises:
            ValueError: If there are zero or multiple measurements for the class
        """

        results = measurements.get(metric_cls, [])
        if len(results) == 0:
            raise ValueError(f"No measurements found for {metric_cls.__name__}")
        if len(results) > 1:
            raise ValueError(
                f"Expected single measurement for {metric_cls.__name__}, "
                f"got {len(results)}"
            )

        return results[0]


class Measurement(BaseModel):
    """
    Result of a metric calculation.

    Holds the metric that produced it, the calculated value, tags, and diagnostic information.
    """

    metric: Metric
    value: Any = None
    tags: dict = Field(default_factory=dict)
    diagnostic: str = ""
