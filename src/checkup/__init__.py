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
from checkup.metric import ExecutorType, Metric, Unit
from checkup.provider import Provider
from checkup.providers.tags import TagProvider
from checkup.types import Context
from checkup.utils import suppress_subprocess_output

# Rebuild models to resolve forward references after all classes are imported
Measurement.model_rebuild()

__all__ = [
    "CheckHub",
    "MeasurementResult",
    "Metric",
    "Measurement",
    "Measurements",
    "ExecutorType",
    "Unit",
    "Provider",
    "TagProvider",
    "Context",
    "ProviderExecutor",
    "MetricCalculator",
    "Materializer",
    "ConsoleMaterializer",
    "CSVMaterializer",
    "HTMLMaterializer",
    "SQLAlchemyMaterializer",
    "ProviderError",
    "MetricPicklingError",
    "DuplicateMetricNameError",
    "suppress_subprocess_output",
]


def main() -> None:
    from checkup.cli import app

    app()
