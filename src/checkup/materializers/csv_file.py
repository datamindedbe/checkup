"""CSV file materializer."""

import csv
from pathlib import Path

from checkup.materializers.base import Materializer
from checkup.metric import Metric


class CSVMaterializer(Materializer):
    """Output metrics to a CSV file.

    Writes metrics data in CSV format for further analysis.
    """

    output_path: Path

    def materialize(self, metrics: list[Metric], direct_metric_names: set[str]) -> None:
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
