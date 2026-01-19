"""Checkup - Extensible metrics calculation framework."""

from checkup.hub import (
    CheckHub,
    DuplicateMetricNameError,
    MeasurementResult,
    MetricPicklingError,
    ProviderError,
)
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

__all__ = [
    "CheckHub",
    "MeasurementResult",
    "Metric",
    "ExecutorType",
    "Provider",
    "TagProvider",
    "Materializer",
    "ConsoleMaterializer",
    "CSVMaterializer",
    "HTMLMaterializer",
    "Context",
    # Exceptions
    "ProviderError",
    "MetricPicklingError",
    "DuplicateMetricNameError",
]


def main() -> None:
    """CLI entry point."""
    print("Checkup metrics framework")
    print("Import CheckHub to get started")
