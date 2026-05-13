"""Console materializer for terminal output."""

from rich.console import Console
from rich.table import Table

from checkup.materializers.base import Materializer
from checkup.measurement import Measurement


class ConsoleMaterializer(Materializer):
    """
    Output measurements to console.

    Outputs a rich table with measurement details.
    Optionally groups measurements by tag values.

    Args:
        group_tags: List of tag names to group by. If empty, no grouping.
        include_indirect: If True, include indirect measurements.
    """

    group_tags: list[str] = []

    def materialize(
        self, measurements: list[Measurement], direct_metric_names: set[str]
    ) -> None:
        """
        Print measurements to console as a rich table, optionally grouped by tags.
        """

        filtered = self._filter_measurements(measurements, direct_metric_names)
        console = Console()

        if not self.group_tags:
            self._print_table(console, filtered, title=None)
            return

        groups = self._group_by_tags(filtered)
        for i, (tag_values, group_measurements) in enumerate(sorted(groups.items())):
            if i > 0:
                console.print()
            title = " | ".join(
                f"{tag}: {value}"
                for tag, value in zip(self.group_tags, tag_values, strict=True)
            )
            self._print_table(console, group_measurements, title=title)

    def _print_table(
        self,
        console: Console,
        measurements: list[Measurement],
        title: str | None,
    ) -> None:
        """
        Print a single table of measurements.
        """

        table = Table(title=title)

        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="dim")
        table.add_column("Value", justify="right", style="green")
        table.add_column("Unit", style="yellow")
        table.add_column("Diagnostics", style="red")

        for measurement in measurements:
            table.add_row(
                measurement.metric.name,
                measurement.metric.description,
                str(measurement.value) if measurement.value is not None else "",
                measurement.metric.unit,
                measurement.diagnostic,
            )

        console.print(table)

    def _group_by_tags(
        self,
        measurements: list[Measurement],
        default: str = "Unknown",
    ) -> dict[tuple[str, ...], list[Measurement]]:
        """
        Group measurements by tag values.
        """

        groups: dict[tuple[str, ...], list[Measurement]] = {}
        for measurement in measurements:
            key = tuple(measurement.tags.get(tag, default) for tag in self.group_tags)
            if key not in groups:
                groups[key] = []
            groups[key].append(measurement)
        return groups
