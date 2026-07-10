"""Markdown materializer for Markdown table output."""

from checkup.materializers.base import Materializer
from checkup.measurement import Measurement

COLUMNS = ("Name", "Description", "Value", "Unit", "Diagnostics")
ALIGNMENTS = ("---", "---", "---:", "---", "---")  # Right-align the Value column.


class MarkdownMaterializer(Materializer):
    """
    Output measurements as a GitHub-flavoured Markdown table.
    """

    def materialize(
        self, measurements: list[Measurement], direct_metric_names: set[str]
    ) -> None:
        """
        Print measurements as a Markdown table.
        """

        filtered = self._filter_measurements(measurements, direct_metric_names)

        rows = [self._row(COLUMNS), self._row(ALIGNMENTS)]
        for measurement in filtered:
            rows.append(
                self._row(
                    (
                        measurement.metric.name,
                        measurement.metric.description,
                        str(measurement.value) if measurement.value is not None else "",
                        measurement.metric.unit,
                        measurement.diagnostic,
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
