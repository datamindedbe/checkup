"""SQLAlchemy database materializer."""

import json
from datetime import UTC, datetime

from pydantic import SecretStr
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

from checkup.materializers.base import Materializer
from checkup.metric import Metric


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
        table_schema: Optional database schema to use (e.g. "analytics", "public").
            If None, uses the database's default schema.
    """

    connection_url: SecretStr
    table_name: str = "metrics"
    table_schema: str | None = None

    def materialize(self, metrics: list[Metric], direct_metric_names: set[str]) -> None:
        """Write metrics to the database."""
        filtered = self._filter_metrics(metrics, direct_metric_names)
        if not filtered:
            return

        engine = create_engine(self.connection_url.get_secret_value())
        metadata = MetaData(schema=self.table_schema)

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
                "tags": json.dumps(metric.tags) if metric.tags is not None else None,
                "measured_at": now,
            }
            for metric in filtered
        ]

        with engine.begin() as conn:
            conn.execute(insert(table), rows)
