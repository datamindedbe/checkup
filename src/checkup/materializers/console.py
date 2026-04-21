"""Console materializer for terminal output."""

from rich.console import Console
from rich.table import Table

from checkup.materializers.base import Materializer, group_measurements_by_tags
from checkup.metric import Measurement


class ConsoleMaterializer(Materializer):
    """Output metrics to console.

    Outputs a rich table with metric details.
    Optionally groups metrics by tag values.
    """

    group_tag_1: str | None = None
    group_tag_2: str | None = None

    def materialize(
        self, measurements: list[Measurement], direct_metric_names: set[str]
    ) -> None:
        """Print measurements to console as a rich table, grouped by tags."""
        filtered = self._filter_measurements(measurements, direct_metric_names)

        console = Console()

        groups = group_measurements_by_tags(
            filtered, self.group_tag_1, self.group_tag_2
        )

        # Create a table for each group
        for (tag1_value, tag2_value), group_measurements in sorted(groups.items()):
            table = Table(
                title=f"{self.group_tag_1}: {tag1_value} | {self.group_tag_2}: {tag2_value}"
            )

            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="dim")
            table.add_column("Value", justify="right", style="green")
            table.add_column("Unit", style="yellow")
            table.add_column("Diagnostics", style="red")

            for measurement in group_measurements:
                table.add_row(
                    measurement.metric.name,
                    measurement.metric.description,
                    str(measurement.value) if measurement.value is not None else "",
                    measurement.metric.unit,
                    measurement.diagnostic,
                )

            console.print(table)
            console.print()  # Add spacing between tables
