"""Materializers for outputting metrics."""

import csv
import json
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Text,
    create_engine,
    insert,
)
from sqlalchemy import (
    Table as SATable,
)

from checkup.metric import Metric


def group_metrics_by_tags(
    metrics: list[Metric],
    tag1: str,
    tag2: str,
    default_value: str = "Unknown",
) -> dict[tuple[str, str], list[Metric]]:
    """Group metrics by two tag values.

    Args:
        metrics: List of metrics to group
        tag1: First tag name for grouping
        tag2: Second tag name for grouping
        default_value: Value to use when tag is missing

    Returns:
        Dict mapping (tag1_value, tag2_value) tuples to metric lists
    """
    groups: dict[tuple[str, str], list[Metric]] = {}
    for metric in metrics:
        tag1_value = metric.tags.get(tag1, default_value)
        tag2_value = metric.tags.get(tag2, default_value)
        key = (tag1_value, tag2_value)

        if key not in groups:
            groups[key] = []
        groups[key].append(metric)

    return groups


def group_metrics_hierarchical(
    metrics: list[Metric],
    tag1: str,
    tag2: str,
    default_value: str = "Ungrouped",
) -> dict[str, dict[str, list[Metric]]]:
    """Group metrics hierarchically by two tag values.

    Args:
        metrics: List of metrics to group
        tag1: First tag name for top-level grouping
        tag2: Second tag name for nested grouping
        default_value: Value to use when tag is missing

    Returns:
        Nested dict: {tag1_value: {tag2_value: [metrics]}}
    """
    grouped: dict[str, dict[str, list[Metric]]] = defaultdict(lambda: defaultdict(list))

    for metric in metrics:
        group1_value = metric.tags.get(tag1, default_value)
        group2_value = metric.tags.get(tag2, default_value)
        grouped[group1_value][group2_value].append(metric)

    return dict(grouped)


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
    def materialize(self, metrics: list[Metric], direct_metric_names: set[str]) -> None:
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

    def materialize(self, metrics: list[Metric], direct_metric_names: set[str]) -> None:
        """Print metrics to console as a rich table, grouped by tags."""
        filtered = self._filter_metrics(metrics, direct_metric_names)

        console = Console()

        groups = group_metrics_by_tags(filtered, self.group_tag_1, self.group_tag_2)

        # Create a table for each group
        for (tag1_value, tag2_value), group_metrics in sorted(groups.items()):
            table = Table(
                title=f"{self.group_tag_1}: {tag1_value} | {self.group_tag_2}: {tag2_value}"
            )

            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="dim")
            table.add_column("Value", justify="right", style="green")
            table.add_column("Unit", style="yellow")
            table.add_column("Diagnostics", style="red")

            for metric in group_metrics:
                table.add_row(
                    metric.name,
                    metric.description,
                    str(metric.value) if metric.value is not None else "",
                    metric.unit,
                    metric.diagnostic,
                )

            console.print(table)
            console.print()  # Add spacing between tables


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


class HTMLMaterializer(Materializer):
    """Output metrics to an HTML file with hierarchical grouping.

    Generates a styled HTML report with metrics grouped by two levels of tags.
    Uses Bootstrap accordions for collapsible groups.

    Attributes:
        output_path: Path where the HTML file will be written
        group_tag_1: Tag name for level 1 grouping (e.g., "domain")
        group_tag_2: Tag name for level 2 grouping (e.g., "project")
    """

    output_path: Path
    group_tag_1: str
    group_tag_2: str

    def materialize(self, metrics: list[Metric], direct_metric_names: set[str]) -> None:
        """Generate and write HTML report to file."""
        filtered = self._filter_metrics(metrics, direct_metric_names)

        # Group metrics hierarchically
        grouped = group_metrics_hierarchical(
            filtered, self.group_tag_1, self.group_tag_2
        )

        # Generate HTML
        html = self._generate_html(grouped)

        # Write to file
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w") as f:
            f.write(html)

    def _generate_html(self, grouped: dict) -> str:
        """Generate complete HTML document using Jinja2 template."""
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        template = env.get_template("metrics_report.html")

        # Render template with data
        return template.render(grouped=grouped)


class SQLAlchemyMaterializer(Materializer):
    """Output metrics to a database via SQLAlchemy.

    Writes metrics as rows to a database table. The table is created
    automatically if it doesn't exist. Rows are appended on each
    materialization, with a ``measured_at`` timestamp to distinguish runs.

    Works with any database supported by SQLAlchemy (SQLite, PostgreSQL,
    MySQL, etc.) via the connection URL.

    Attributes:
        connection_url: SQLAlchemy connection URL (e.g. "sqlite:///metrics.db",
            "postgresql://user:pass@host/db")
        table_name: Name of the target table (default: "metrics")
    """

    connection_url: str
    table_name: str = "metrics"

    def materialize(self, metrics: list[Metric], direct_metric_names: set[str]) -> None:
        """Write metrics to the database."""
        filtered = self._filter_metrics(metrics, direct_metric_names)
        if not filtered:
            return

        engine = create_engine(self.connection_url)
        metadata = MetaData()

        table = SATable(
            self.table_name,
            metadata,
            Column("name", String(255), nullable=False),
            Column("value", String(255)),
            Column("unit", String(255)),
            Column("diagnostic", Text),
            Column("description", Text),
            Column("tags", Text),
            Column("measured_at", DateTime, nullable=False),
        )

        metadata.create_all(engine)

        now = datetime.now(UTC)
        rows = [
            {
                "name": metric.name,
                "value": str(metric.value) if metric.value is not None else None,
                "unit": metric.unit,
                "diagnostic": metric.diagnostic,
                "description": metric.description,
                "tags": json.dumps(metric.tags) if metric.tags else None,
                "measured_at": now,
            }
            for metric in filtered
        ]

        with engine.begin() as conn:
            conn.execute(insert(table), rows)
