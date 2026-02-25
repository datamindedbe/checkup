"""Checkup - Extensible metrics calculation framework."""

from checkup.errors import (
    DuplicateMetricNameError,
    MetricPicklingError,
    ProviderError,
)
from checkup.executor import MetricCalculator, ProviderExecutor
from checkup.hub import CheckHub, MeasurementResult
from checkup.materializers import (
    ConsoleMaterializer,
    CSVMaterializer,
    HTMLMaterializer,
    Materializer,
)
from checkup.metric import ExecutorType, Metric
from checkup.provider import Provider
from checkup.providers.tags import TagProvider
from checkup.types import Context
from checkup.utils import suppress_subprocess_output

__all__ = [
    # Core
    "CheckHub",
    "MeasurementResult",
    "Metric",
    "ExecutorType",
    "Provider",
    "TagProvider",
    "Context",
    # Executors
    "ProviderExecutor",
    "MetricCalculator",
    # Materializers
    "Materializer",
    "ConsoleMaterializer",
    "CSVMaterializer",
    "HTMLMaterializer",
    # Exceptions
    "ProviderError",
    "MetricPicklingError",
    "DuplicateMetricNameError",
    # Utilities
    "suppress_subprocess_output",
]


def main() -> None:
    """CLI entry point."""
    print("Checkup metrics framework")
    print("Import CheckHub to get started")
