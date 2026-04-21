"""Console materializer for terminal output."""

from pydantic import field_validator
from rich.console import Console
from rich.table import Table

from checkup.materializers.base import Materializer
from checkup.metric import Measurement


class ConsoleMaterializer(Materializer):
    """
    Output measurements to console.

    Outputs a rich table with measurement details.
    Optionally groups measurements by tag values (max 2 levels).

    Args:
        group_tags: List of tag names to group by (max 2). If empty, no grouping.
        include_indirect: If True, include indirect measurements.
    """

    group_tags: list[str] = []

    @field_validator("group_tags")
    @classmethod
    def validate_group_tags(cls, v: list[str]) -> list[str]:
        if len(v) > 2:
            raise ValueError(f"Maximum 2 group tags supported, got {len(v)}: {v}")
        return v

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
        elif len(self.group_tags) == 1:
            groups = self._group_by_single_tag(filtered, self.group_tags[0])
            for tag_value, group_measurements in sorted(groups.items()):
                title = f"{self.group_tags[0]}: {tag_value}"
                self._print_table(console, group_measurements, title=title)
                console.print()
        else:
            groups = self._group_by_two_tags(
                filtered, self.group_tags[0], self.group_tags[1]
            )
            for (tag1_value, tag2_value), group_measurements in sorted(groups.items()):
                title = f"{self.group_tags[0]}: {tag1_value} | {self.group_tags[1]}: {tag2_value}"
                self._print_table(console, group_measurements, title=title)
                console.print()

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

    def _group_by_single_tag(
        self,
        measurements: list[Measurement],
        tag: str,
        default: str = "Unknown",
    ) -> dict[str, list[Measurement]]:
        """
        Group measurements by a single tag value.
        """

        groups: dict[str, list[Measurement]] = {}
        for measurement in measurements:
            key = measurement.tags.get(tag, default)
            if key not in groups:
                groups[key] = []
            groups[key].append(measurement)
        return groups

    def _group_by_two_tags(
        self,
        measurements: list[Measurement],
        tag1: str,
        tag2: str,
        default: str = "Unknown",
    ) -> dict[tuple[str, str], list[Measurement]]:
        """
        Group measurements by two tag values.
        """

        groups: dict[tuple[str, str], list[Measurement]] = {}
        for measurement in measurements:
            key = (
                measurement.tags.get(tag1, default),
                measurement.tags.get(tag2, default),
            )
            if key not in groups:
                groups[key] = []
            groups[key].append(measurement)
        return groups
