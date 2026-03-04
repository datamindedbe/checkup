"""SQLAlchemy database materializer."""

import json
from datetime import UTC, datetime
from typing import Any

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
        connect_args: Optional dict of arguments passed to the underlying DB-API
            driver via SQLAlchemy's connect_args.
        expand_tags: If True, expand tags into separate columns named ``tag_<key>``
            instead of storing them as JSON in a single ``tags`` column.
        batch_size: Number of rows to insert per batch (default: 1000). Useful for
            databases with query size limits.
    """

    connection_url: SecretStr
    table_name: str = "metrics"
    table_schema: str | None = None
    connect_args: dict[str, Any] | None = None
    expand_tags: bool = False
    batch_size: int = 1000

    def materialize(self, metrics: list[Metric], direct_metric_names: set[str]) -> None:
        """Write metrics to the database."""
        filtered = self._filter_metrics(metrics, direct_metric_names)
        if not filtered:
            return

        engine = create_engine(
            self.connection_url.get_secret_value(),
            connect_args=self.connect_args or {},
        )
        metadata = MetaData(schema=self.table_schema)

        base_columns = [
            Column("name", String(255), nullable=False),
            Column("value", String(255)),
            Column("unit", String(255)),
            Column("diagnostic", Text),
            Column("description", Text),
        ]

        if self.expand_tags:
            tag_keys = {
                key for metric in filtered if metric.tags for key in metric.tags
            }
            tag_columns = [
                Column(f"tag_{key}", String(255)) for key in sorted(tag_keys)
            ]
        else:
            tag_keys = set()
            tag_columns = [Column("tags", Text)]

        table = SATable(
            self.table_name,
            metadata,
            *base_columns,
            *tag_columns,
            Column("measured_at", DateTime, nullable=False),
        )

        metadata.create_all(engine)

        now = datetime.now(UTC)
        rows = []
        for metric in filtered:
            row = {
                "name": metric.name,
                "value": str(metric.value) if metric.value is not None else None,
                "unit": metric.unit,
                "diagnostic": metric.diagnostic,
                "description": metric.description,
                "measured_at": now,
            }
            if self.expand_tags:
                for key in tag_keys:
                    row[f"tag_{key}"] = metric.tags.get(key) if metric.tags else None
            else:
                row["tags"] = (
                    json.dumps(metric.tags) if metric.tags is not None else None
                )
            rows.append(row)

        with engine.begin() as conn:
            for i in range(0, len(rows), self.batch_size):
                batch = rows[i : i + self.batch_size]
                conn.execute(insert(table), batch)
