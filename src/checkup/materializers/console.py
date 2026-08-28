"""Console materializer for terminal output."""

from rich.console import Console
from rich.table import Table

from checkup.materializers.base import Materializer
from checkup.materializers.utils import (
    TableColumn,
    effective_columns,
    render_cell,
)
from checkup.measurement import Measurement
from checkup.metric import Unit

# Rich column settings.
COLUMN_SETTINGS: dict[TableColumn, dict] = {
    "name": {"header": "Name", "style": "cyan", "no_wrap": True},
    "description": {"header": "Description", "style": "dim"},
    "value": {"header": "Value", "justify": "right", "style": "green"},
    "unit": {"header": "Unit", "style": "yellow"},
    "diagnostics": {"header": "Diagnostics", "style": "red"},
}


class ConsoleMaterializer(Materializer):
    """
    Output measurements to console.

    Outputs a rich table with measurement details.
    Optionally groups measurements by tag values.

    Args:
        group_tags: List of tag names to group by. If empty, no grouping.
        include_indirect: If True, include indirect measurements.
        pretty: If True, format values for presentation, well-know ``Metric.Unit`` values are formatted accordingly.
        columns: Columns to display, in order. Defaults to all columns.
    """

    group_tags: list[str] = []
    pretty: bool = False
    columns: list[TableColumn] | None = None

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

        columns = effective_columns(self.columns, self.pretty)

        table = Table(title=title)
        for column in columns:
            table.add_column(**COLUMN_SETTINGS[column])

        for measurement in measurements:
            table.add_row(
                *(self._cell(measurement, column, columns) for column in columns)
            )

        console.print(table)

    def _cell(
        self,
        measurement: Measurement,
        column: TableColumn,
        columns: tuple[TableColumn, ...],
    ) -> str:
        text = render_cell(measurement, column, columns, self.pretty)

        # Pretty booleans are colored.
        if (
            self.pretty
            and column == "value"
            and measurement.value is not None
            and measurement.metric.unit == Unit.BOOLEAN
        ):
            color = "green" if measurement.value else "red"
            return f"[{color}]{text}[/{color}]"
        return text

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
