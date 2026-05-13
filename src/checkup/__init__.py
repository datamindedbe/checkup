"""Checkup - Computational governance framework for measuring data product health."""

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
    SQLAlchemyMaterializer,
)
from checkup.measurement import Measurement, Measurements
from checkup.metric import ExecutorType, Metric
from checkup.provider import Provider
from checkup.providers.tags import TagProvider
from checkup.types import Context
from checkup.utils import suppress_subprocess_output

# Rebuild models to resolve forward references after all classes are imported
Measurement.model_rebuild()

__all__ = [
    # Core
    "CheckHub",
    "MeasurementResult",
    "Metric",
    "Measurement",
    "Measurements",
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
    "SQLAlchemyMaterializer",
    # Exceptions
    "ProviderError",
    "MetricPicklingError",
    "DuplicateMetricNameError",
    # Utilities
    "suppress_subprocess_output",
]


def main() -> None:
    from checkup.cli import app

    app()
