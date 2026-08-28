import json

from fixtures import DummyMetric, IndirectDummyMetric, OtherDummyMetric
from sqlalchemy import create_engine, text

from checkup.materializers import SQLAlchemyMaterializer


def test_sqlalchemy_materializer(tmp_path):
    """Test SQLAlchemy materializer writes measurements to database."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=42, tags={"domain": "Analytics"})

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
    )
    materializer.materialize([measurement], {"dummy"})

    # Verify data was written
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 1
    row = rows[0]
    assert row[0] == "dummy"  # name
    assert row[1] == "42"  # value
    assert row[2] == "count"  # unit
    assert row[5] == json.dumps({"domain": "Analytics"})  # tags
    assert row[6] is not None  # measured_at


def test_sqlalchemy_materializer_multiple_metrics(tmp_path):
    """Test SQLAlchemy materializer with multiple measurements."""
    metric1 = DummyMetric(expected_value=42)
    measurement1 = metric1.measure(value=42)

    metric2 = OtherDummyMetric(expected_value=100)
    measurement2 = metric2.measure(value=100)

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
    )
    materializer.materialize([measurement1, measurement2], {"dummy", "other_metric"})

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 2
    names = {row[0] for row in rows}
    assert names == {"dummy", "other_metric"}


def test_sqlalchemy_materializer_appends_rows(tmp_path):
    """Test that successive materializations append rows."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=42)

    db_path = tmp_path / "metrics.db"
    url = f"sqlite:///{db_path}"
    materializer = SQLAlchemyMaterializer(connection_url=url)

    # Materialize twice
    materializer.materialize([measurement], {"dummy"})
    materializer.materialize([measurement], {"dummy"})

    engine = create_engine(url)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 2


def test_sqlalchemy_materializer_custom_table_name(tmp_path):
    """Test SQLAlchemy materializer with custom table name."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=42)

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
        table_name="checkup_results",
    )
    materializer.materialize([measurement], {"dummy"})

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM checkup_results")).fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "dummy"


def test_sqlalchemy_materializer_filters_indirect(tmp_path):
    """Test SQLAlchemy materializer filtering of indirect measurements."""
    direct_metric = DummyMetric(expected_value=42)
    direct_measurement = direct_metric.measure(value=42)

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_measurement = indirect_metric.measure(value=100)

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
    )
    materializer.materialize([direct_measurement, indirect_measurement], {"dummy"})

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "dummy"


def test_sqlalchemy_materializer_includes_indirect(tmp_path):
    """Test SQLAlchemy materializer including indirect measurements."""
    direct_metric = DummyMetric(expected_value=42)
    direct_measurement = direct_metric.measure(value=42)

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_measurement = indirect_metric.measure(value=100)

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
        include_indirect=True,
    )
    materializer.materialize([direct_measurement, indirect_measurement], {"dummy"})

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 2
    names = {row[0] for row in rows}
    assert names == {"dummy", "indirect"}


def test_sqlalchemy_materializer_none_value(tmp_path):
    """Test SQLAlchemy materializer handles None values."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=None, tags={})

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
    )
    materializer.materialize([measurement], {"dummy"})

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 1
    assert rows[0][1] is None  # value should be None


def test_sqlalchemy_materializer_empty_metrics(tmp_path):
    """Test SQLAlchemy materializer with no metrics does nothing."""
    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
    )
    materializer.materialize([], {"dummy"})

    # Database file should not be created
    assert not db_path.exists()


def test_sqlalchemy_materializer_table_schema():
    """Test that table_schema is stored and wired through to DDL."""
    from sqlalchemy import Column, MetaData, String
    from sqlalchemy import Table as SATable
    from sqlalchemy.schema import CreateTable

    materializer = SQLAlchemyMaterializer(
        connection_url="sqlite:///:memory:",
        table_schema="analytics",
    )
    assert materializer.table_schema == "analytics"

    # Verify schema appears in the generated DDL
    metadata = MetaData(schema="analytics")
    table = SATable("metrics", metadata, Column("name", String(255)))
    ddl = str(
        CreateTable(table).compile(dialect=create_engine("sqlite:///:memory:").dialect)
    )
    assert "analytics." in ddl


def test_sqlalchemy_materializer_table_schema_default_is_none():
    """Test that table_schema defaults to None."""
    materializer = SQLAlchemyMaterializer(
        connection_url="sqlite:///:memory:",
    )
    assert materializer.table_schema is None


def test_sqlalchemy_materializer_expand_tags(tmp_path):
    """Test SQLAlchemy materializer expands tags into separate columns."""
    metric1 = DummyMetric(expected_value=42)
    measurement1 = metric1.measure(
        value=42, tags={"domain": "Analytics", "env": "prod"}
    )

    metric2 = OtherDummyMetric(expected_value=100)
    measurement2 = metric2.measure(
        value=100, tags={"domain": "Engineering", "team": "platform"}
    )

    metric3 = IndirectDummyMetric(expected_value=50)
    measurement3 = metric3.measure(value=50, tags={})

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
        expand_tags=True,
        include_indirect=True,
    )
    materializer.materialize(
        [measurement1, measurement2, measurement3], {"dummy", "other_metric"}
    )

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(metrics)"))
        columns = {row[1] for row in result.fetchall()}

    # All unique tag keys should have columns, tags column should be omitted
    assert "tag_domain" in columns
    assert "tag_env" in columns
    assert "tag_team" in columns
    assert "tags" not in columns

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT name, tag_domain, tag_env, tag_team FROM metrics ORDER BY name"
            )
        ).fetchall()

    assert len(rows) == 3

    # dummy metric
    assert rows[0][0] == "dummy"
    assert rows[0][1] == "Analytics"
    assert rows[0][2] == "prod"
    assert rows[0][3] is None  # team not in measurement1

    # indirect metric (no tags)
    assert rows[1][0] == "indirect"
    assert rows[1][1] is None
    assert rows[1][2] is None
    assert rows[1][3] is None

    # other_metric
    assert rows[2][0] == "other_metric"
    assert rows[2][1] == "Engineering"
    assert rows[2][2] is None  # env not in measurement2
    assert rows[2][3] == "platform"


def test_sqlalchemy_materializer_expand_tags_no_tags(tmp_path):
    """Test expand_tags handles measurements with no tags."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=42, tags={})

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
        expand_tags=True,
    )
    materializer.materialize([measurement], {"dummy"})

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(metrics)"))
        columns = {row[1] for row in result.fetchall()}

    # No tag columns should be created
    assert not any(col.startswith("tag_") for col in columns)
    assert "tags" not in columns

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 1


def test_sqlalchemy_materializer_batch_size(tmp_path):
    """Test SQLAlchemy materializer respects batch_size for large inserts."""
    # Create more measurements than the batch size
    measurements = []
    for i in range(25):
        metric = DummyMetric(expected_value=i)
        measurement = metric.measure(value=i)
        measurements.append(measurement)

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
        batch_size=10,  # Small batch size to test batching
    )
    materializer.materialize(measurements, {"dummy"})

    # Verify all rows were inserted
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 25
    values = {int(row[1]) for row in rows}
    assert values == set(range(25))
