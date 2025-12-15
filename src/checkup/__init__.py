"""Checkup - Extensible metrics calculation framework."""
from checkup.hub import CheckHub, MeasurementResult
from checkup.materializers import ConsoleMaterializer, CSVMaterializer, Materializer
from checkup.metric import Metric
from checkup.types import Context, ContextDict

__all__ = [
    "CheckHub",
    "MeasurementResult",
    "Metric",
    "Materializer",
    "ConsoleMaterializer",
    "CSVMaterializer",
    "Context",
    "ContextDict",
]


def main() -> None:
    """CLI entry point."""
    print("Checkup metrics framework")
    print("Import CheckHub to get started")
