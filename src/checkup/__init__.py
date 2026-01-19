"""Checkup - Extensible metrics calculation framework."""

from checkup.errors import (
    DuplicateMetricNameError,
    MetricPicklingError,
    ProviderError,
)
from checkup.executor import MetricCalculator, ProviderExecutor
from checkup.hub import CheckUp, MeasurementResult
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
    # Core
    "CheckUp",
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
]
