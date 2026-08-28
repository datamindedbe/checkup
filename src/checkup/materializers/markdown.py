"""Markdown materializer for Markdown table output."""

from checkup.materializers.base import Materializer
from checkup.materializers.utils import (
    TableColumn,
    effective_columns,
    render_cell,
)
from checkup.measurement import Measurement

HEADERS: dict[TableColumn, str] = {
    "name": "Name",
    "description": "Description",
    "value": "Value",
    "unit": "Unit",
    "diagnostics": "Diagnostics",
}

ALIGNMENTS: dict[TableColumn, str] = {
    "name": "---",
    "description": "---",
    "value": "---:",  # Right-align
    "unit": "---",
    "diagnostics": "---",
}


class MarkdownMaterializer(Materializer):
    """
    Output measurements as a GitHub-flavoured Markdown table.

    Args:
        include_indirect: If True, include indirect measurements.
        pretty: If True, format values for presentation, well-know ``Metric.Unit`` values are formatted accordingly.
        columns: Columns to display, in order. Defaults to all columns.
    """

    pretty: bool = False
    columns: list[TableColumn] | None = None

    def materialize(
        self, measurements: list[Measurement], direct_metric_names: set[str]
    ) -> None:
        """
        Print measurements as a Markdown table.
        """

        filtered = self._filter_measurements(measurements, direct_metric_names)
        columns = effective_columns(self.columns, self.pretty)

        rows = [
            self._row(tuple(HEADERS[column] for column in columns)),
            self._row(tuple(ALIGNMENTS[column] for column in columns)),
        ]
        for measurement in filtered:
            rows.append(
                self._row(
                    tuple(
                        render_cell(measurement, column, columns, self.pretty)
                        for column in columns
                    )
                )
            )
        print("\n".join(rows))

    @classmethod
    def _row(cls, cells: tuple[str, ...]) -> str:
        return "| " + " | ".join(cls._cell(cell) for cell in cells) + " |"

    @staticmethod
    def _cell(value: str) -> str:
        """
        Escape a value for a Markdown table cell.

        Cells cannot contain a raw pipe (column separator) or newline (row separator),
        so escape pipes and turn newlines into `<br>`.
        """

        return str(value or "").replace("|", "\\|").replace("\n", "<br>").strip()
