"""Console materializer for terminal output."""

from rich.console import Console
from rich.table import Table

from checkup.materializers.base import Materializer, group_metrics_by_tags
from checkup.metric import Metric


class ConsoleMaterializer(Materializer):
    """Output metrics to console.

    Outputs a rich table with metric details.
    Optionally groups metrics by tag values.
    """

    group_tag_1: str | None = None
    group_tag_2: str | None = None

    def materialize(self, metrics: list[Metric], direct_metric_names: set[str]) -> None:
        """Print metrics to console as a rich table, optionally grouped by tags."""
        filtered = self._filter_metrics(metrics, direct_metric_names)
        console = Console()

        if self.group_tag_1 and self.group_tag_2:
            groups = group_metrics_by_tags(filtered, self.group_tag_1, self.group_tag_2)
            for (tag1_value, tag2_value), group_metrics in sorted(groups.items()):
                title = f"{self.group_tag_1}: {tag1_value} | {self.group_tag_2}: {tag2_value}"
                self._print_table(console, group_metrics, title)
                console.print()
        else:
            self._print_table(console, filtered, "Metrics")

    def _print_table(self, console: Console, metrics: list[Metric], title: str) -> None:
        """Print a metrics table."""
        table = Table(title=title)

        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="dim")
        table.add_column("Value", justify="right", style="green")
        table.add_column("Unit", style="yellow")
        table.add_column("Diagnostics", style="red")

        for metric in metrics:
            table.add_row(
                metric.name,
                metric.description,
                str(metric.value) if metric.value is not None else "",
                metric.unit,
                metric.diagnostic,
            )

        console.print(table)
