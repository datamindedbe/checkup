"""CSV file materializer."""

import csv
from pathlib import Path

from checkup.materializers.base import Materializer
from checkup.measurement import Measurement


class CSVMaterializer(Materializer):
    """Output measurements to a CSV file.

    Writes measurement data in CSV format for further analysis.
    """

    output_path: Path

    def materialize(
        self, measurements: list[Measurement], direct_metric_names: set[str]
    ) -> None:
        """Write measurements to CSV file."""
        filtered = self._filter_measurements(measurements, direct_metric_names)

        with open(self.output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "value", "unit", "diagnostic", "description"])

            for m in filtered:
                writer.writerow(
                    [
                        m.metric.name,
                        m.value,
                        m.metric.unit,
                        m.diagnostic,
                        m.metric.description,
                    ]
                )
