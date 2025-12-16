"""Materializers for outputting metrics."""

import csv
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel

from checkup.metric import Metric


class Materializer(ABC, BaseModel):
    """Base class for metric materializers.

    Materializers format and output metrics to various formats.

    Attributes:
        include_indirect: If True, include metrics that were auto-added as
            dependencies. If False (default), only include directly requested metrics.
    """

    include_indirect: bool = False

    def _filter_metrics(
        self, metrics: list[Metric], direct_metric_names: set[str]
    ) -> list[Metric]:
        """Filter metrics based on include_indirect setting.

        Args:
            metrics: List of all calculated metrics
            direct_metric_names: Set of names of directly requested metrics

        Returns:
            Filtered list of metrics
        """
        if self.include_indirect:
            return metrics
        return [m for m in metrics if m.name in direct_metric_names]

    @abstractmethod
    def materialize(
        self, metrics: list[Metric], direct_metric_names: set[str]
    ) -> None:
        """Format and output metrics.

        Args:
            metrics: List of calculated metrics
            direct_metric_names: Set of names of directly requested metrics
        """
        pass


class ConsoleMaterializer(Materializer):
    """Output metrics to console.

    Simple text output for debugging and quick checks.
    """

    def materialize(
        self, metrics: list[Metric], direct_metric_names: set[str]
    ) -> None:
        """Print metrics to console."""
        filtered = self._filter_metrics(metrics, direct_metric_names)

        print("\n=== Metrics Report ===\n")

        for metric in filtered:
            print(f"{metric.name}: {metric.value} {metric.unit}")
            if metric.description:
                print(f"  {metric.description}")
            print()


class CSVMaterializer(Materializer):
    """Output metrics to a CSV file.

    Writes metrics data in CSV format for further analysis.
    """

    output_path: Path

    def materialize(
        self, metrics: list[Metric], direct_metric_names: set[str]
    ) -> None:
        """Write metrics to CSV file."""
        filtered = self._filter_metrics(metrics, direct_metric_names)

        with open(self.output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "value", "unit", "diagnostic", "description"])

            for metric in filtered:
                writer.writerow(
                    [
                        metric.name,
                        metric.value,
                        metric.unit,
                        metric.diagnostic,
                        metric.description,
                    ]
                )
