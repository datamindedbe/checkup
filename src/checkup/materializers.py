"""Materializers for outputting metrics."""

import csv
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

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

    Outputs a rich table with metric details.
    """

    group_tag_1: str
    group_tag_2: str

    def materialize(
        self, metrics: list[Metric], direct_metric_names: set[str]
    ) -> None:
        """Print metrics to console as a rich table, grouped by tags."""
        filtered = self._filter_metrics(metrics, direct_metric_names)

        console = Console()

        # Group metrics by group_tag_1 and group_tag_2 values
        groups = {}
        for metric in filtered:
            tag1_value = metric.tags.get(self.group_tag_1, "Unknown")
            tag2_value = metric.tags.get(self.group_tag_2, "Unknown")
            group_key = (tag1_value, tag2_value)

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(metric)

        # Create a table for each group
        for (tag1_value, tag2_value), group_metrics in sorted(groups.items()):
            table = Table(title=f"{self.group_tag_1}: {tag1_value} | {self.group_tag_2}: {tag2_value}")

            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="dim")
            table.add_column("Value", justify="right", style="green")
            table.add_column("Unit", style="yellow")
            table.add_column("Diagnostics", style="red")
            table.add_column("Tags", style="magenta")

            for metric in group_metrics:
                tags_str = ", ".join(f"{k}={v}" for k, v in metric.tags.items())
                table.add_row(
                    metric.name,
                    metric.description,
                    str(metric.value) if metric.value is not None else "",
                    metric.unit,
                    metric.diagnostic,
                    tags_str,
                )

            console.print(table)
            console.print()  # Add spacing between tables


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
