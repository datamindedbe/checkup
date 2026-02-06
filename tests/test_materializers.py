"""Tests for materializers."""

import json
import sys
from io import StringIO

import pytest
from conftest import DummyMetric
from sqlalchemy import create_engine, text

from checkup.materializers import (
    ConsoleMaterializer,
    CSVMaterializer,
    HTMLMaterializer,
    Materializer,
    SQLAlchemyMaterializer,
)


def test_materializer_is_abstract():
    """Test that Materializer cannot be instantiated."""
    with pytest.raises(TypeError):
        Materializer()


def test_console_materializer():
    """Test console output materializer."""
    metric = DummyMetric(expected_value=42)
    metric.value = 42

    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    materializer = ConsoleMaterializer(group_tag_1="domain", group_tag_2="project")
    materializer.materialize([metric], {"dummy"})

    # Reset stdout
    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    assert "dummy" in output
    assert "42" in output


def test_csv_materializer(tmp_path):
    """Test CSV file materializer."""
    metric = DummyMetric(expected_value=42)
    metric.value = 42

    output_file = tmp_path / "metrics.csv"
    materializer = CSVMaterializer(output_path=output_file)
    materializer.materialize([metric], {"dummy"})

    # Read and verify CSV content
    content = output_file.read_text()
    lines = content.strip().split("\n")

    # Check header
    assert lines[0] == "name,value,unit,diagnostic,description"

    # Check data row
    assert "dummy" in lines[1]
    assert "42" in lines[1]
    assert "count" in lines[1]


def test_csv_materializer_multiple_metrics(tmp_path):
    """Test CSV materializer with multiple metrics."""
    from conftest import OtherDummyMetric

    metric1 = DummyMetric(expected_value=42)
    metric1.value = 42

    metric2 = OtherDummyMetric(expected_value=100)
    metric2.value = 100

    output_file = tmp_path / "metrics.csv"
    materializer = CSVMaterializer(output_path=output_file)
    materializer.materialize([metric1, metric2], {"dummy", "other_metric"})

    content = output_file.read_text()
    lines = content.strip().split("\n")

    assert len(lines) == 3  # Header + 2 data rows
    assert "dummy" in lines[1]
    assert "other_metric" in lines[2]


def test_materializer_filters_indirect_by_default():
    """Test that materializers filter out indirect metrics by default."""
    from conftest import IndirectDummyMetric

    direct_metric = DummyMetric(expected_value=42)
    direct_metric.value = 42

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_metric.value = 100

    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    materializer = ConsoleMaterializer(group_tag_1="domain", group_tag_2="project")
    # Only "dummy" is direct, "indirect" is not
    materializer.materialize([direct_metric, indirect_metric], {"dummy"})

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    assert "dummy" in output  # Direct metric included
    assert "indirect" not in output  # Indirect metric filtered out


def test_materializer_includes_indirect_when_configured():
    """Test that materializers can include indirect metrics."""
    from conftest import IndirectDummyMetric

    direct_metric = DummyMetric(expected_value=42)
    direct_metric.value = 42

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_metric.value = 100

    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    materializer = ConsoleMaterializer(
        include_indirect=True, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([direct_metric, indirect_metric], {"dummy"})

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    assert "dummy" in output  # Direct metric included
    assert "indirect" in output  # Indirect metric also included


def test_csv_materializer_filters_indirect(tmp_path):
    """Test CSV materializer filtering of indirect metrics."""
    from conftest import IndirectDummyMetric

    direct_metric = DummyMetric(expected_value=42)
    direct_metric.value = 42

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_metric.value = 100

    output_file = tmp_path / "metrics.csv"

    # Default: filter indirect
    materializer = CSVMaterializer(output_path=output_file)
    # Only "dummy" is direct
    materializer.materialize([direct_metric, indirect_metric], {"dummy"})

    content = output_file.read_text()
    lines = content.strip().split("\n")

    assert len(lines) == 2  # Header + 1 direct metric
    assert "dummy" in lines[1]
    assert "indirect" not in content


def test_csv_materializer_includes_indirect(tmp_path):
    """Test CSV materializer including indirect metrics."""
    from conftest import IndirectDummyMetric

    direct_metric = DummyMetric(expected_value=42)
    direct_metric.value = 42

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_metric.value = 100

    output_file = tmp_path / "metrics.csv"

    # With include_indirect=True
    materializer = CSVMaterializer(output_path=output_file, include_indirect=True)
    materializer.materialize([direct_metric, indirect_metric], {"dummy"})

    content = output_file.read_text()
    lines = content.strip().split("\n")

    assert len(lines) == 3  # Header + 2 metrics
    assert "dummy" in content
    assert "indirect" in content


def test_html_materializer(tmp_path):
    """Test HTML materializer with hierarchical grouping."""
    # Create metrics with tags
    metric1 = DummyMetric(expected_value=42)
    metric1.value = 42
    metric1.tags = {"domain": "Analytics", "project": "Project A"}

    metric2 = DummyMetric(expected_value=100)
    metric2.value = 100
    metric2.tags = {"domain": "Analytics", "project": "Project B"}

    metric3 = DummyMetric(expected_value=75)
    metric3.value = 75
    metric3.tags = {"domain": "Engineering", "project": "Project C"}

    output_file = tmp_path / "metrics.html"
    materializer = HTMLMaterializer(
        output_path=output_file, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([metric1, metric2, metric3], {"dummy"})

    # Verify file was created
    assert output_file.exists()

    # Read and verify HTML content
    content = output_file.read_text()

    # Check HTML structure
    assert "<!DOCTYPE html>" in content
    assert "<html lang='en'>" in content
    assert "<title>Metrics Report</title>" in content

    # Check Bootstrap is included
    assert "bootstrap" in content

    # Check for group names
    assert "Analytics" in content
    assert "Engineering" in content
    assert "Project A" in content
    assert "Project B" in content
    assert "Project C" in content

    # Check for accordion components
    assert "accordion" in content
    assert "accordion-button" in content
    assert "accordion-collapse" in content

    # Check metric data is present
    assert "dummy" in content
    assert "42" in content
    assert "100" in content
    assert "75" in content

    # Check for table structure
    assert "<table" in content
    assert "<thead" in content
    assert "<tbody" in content
    assert "Metric</th>" in content
    assert "Value</th>" in content


def test_html_materializer_with_diagnostics(tmp_path):
    """Test HTML materializer with diagnostic coloring."""
    # Create metrics with different diagnostics
    metric1 = DummyMetric(expected_value=42)
    metric1.value = 42
    metric1.diagnostic = "✅ All good"
    metric1.tags = {"domain": "Test", "project": "TestProject"}

    metric2 = DummyMetric(expected_value=100)
    metric2.value = 100
    metric2.diagnostic = "⚠ Warning: something to check"
    metric2.tags = {"domain": "Test", "project": "TestProject"}

    output_file = tmp_path / "metrics.html"
    materializer = HTMLMaterializer(
        output_path=output_file, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([metric1, metric2], {"dummy"})

    content = output_file.read_text()

    # Check for diagnostic color classes
    assert "table-success" in content
    assert "table-warning" in content

    # Check diagnostic text is present
    assert "All good" in content
    assert "Warning" in content


def test_html_materializer_ungrouped_metrics(tmp_path):
    """Test HTML materializer with metrics missing tags."""
    # Create metric without tags
    metric = DummyMetric(expected_value=42)
    metric.value = 42
    metric.tags = {}  # No tags

    output_file = tmp_path / "metrics.html"
    materializer = HTMLMaterializer(
        output_path=output_file, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([metric], {"dummy"})

    content = output_file.read_text()

    # Should default to "Ungrouped"
    assert "Ungrouped" in content
    assert "dummy" in content


def test_html_materializer_filters_indirect(tmp_path):
    """Test HTML materializer filtering of indirect metrics."""
    from conftest import IndirectDummyMetric

    direct_metric = DummyMetric(expected_value=42)
    direct_metric.value = 42
    direct_metric.tags = {"domain": "Test", "project": "TestProject"}

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_metric.value = 100
    indirect_metric.tags = {"domain": "Test", "project": "TestProject"}

    output_file = tmp_path / "metrics.html"

    # Default: filter indirect
    materializer = HTMLMaterializer(
        output_path=output_file, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([direct_metric, indirect_metric], {"dummy"})

    content = output_file.read_text()

    # Only direct metric should be present
    assert "dummy" in content
    assert "indirect" not in content


def test_html_materializer_escape_html(tmp_path):
    """Test that HTML special characters are escaped."""
    metric = DummyMetric(expected_value=42)
    metric.value = "<script>alert('xss')</script>"
    metric.diagnostic = "Test & verify <tags>"
    metric.tags = {"domain": "Test & Dev", "project": "Project <A>"}

    output_file = tmp_path / "metrics.html"
    materializer = HTMLMaterializer(
        output_path=output_file, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([metric], {"dummy"})

    content = output_file.read_text()

    # Check that special characters are escaped
    assert "&lt;script&gt;" in content
    assert "&amp;" in content
    assert "<script>alert" not in content  # Raw script should not be present


def test_html_materializer_end_to_end(tmp_path):
    """End-to-end test with multiple metrics grouped by domain and project.

    This test creates a realistic scenario with multiple domains and projects,
    generates the HTML, and opens it for visual inspection.
    """
    from conftest import OtherDummyMetric

    # Create metrics for Analytics domain
    metric1 = DummyMetric(expected_value=42)
    metric1.value = 42
    metric1.diagnostic = "✅ Good coverage"
    metric1.tags = {"domain": "Analytics", "project": "Customer Insights"}

    metric2 = OtherDummyMetric(expected_value=85)
    metric2.value = 85
    metric2.diagnostic = ""
    metric2.tags = {"domain": "Analytics", "project": "Customer Insights"}

    metric3 = DummyMetric(expected_value=100)
    metric3.value = 100
    metric3.diagnostic = "✅ Excellent"
    metric3.tags = {"domain": "Analytics", "project": "Sales Dashboard"}

    metric4 = OtherDummyMetric(expected_value=60)
    metric4.value = 60
    metric4.diagnostic = "⚠ Below target"
    metric4.tags = {"domain": "Analytics", "project": "Sales Dashboard"}

    # Create metrics for Engineering domain
    metric5 = DummyMetric(expected_value=95)
    metric5.value = 95
    metric5.diagnostic = "✅ Strong test coverage"
    metric5.tags = {"domain": "Engineering", "project": "Core Platform"}

    metric6 = OtherDummyMetric(expected_value=45)
    metric6.value = 45
    metric6.diagnostic = "❌ Critical - needs attention"
    metric6.tags = {"domain": "Engineering", "project": "Core Platform"}

    metric7 = DummyMetric(expected_value=78)
    metric7.value = 78
    metric7.diagnostic = ""
    metric7.tags = {"domain": "Engineering", "project": "Mobile App"}

    # Create metrics for Data Science domain
    metric8 = DummyMetric(expected_value=92)
    metric8.value = 92
    metric8.diagnostic = "✅ Model accuracy within range"
    metric8.tags = {"domain": "Data Science", "project": "ML Pipeline"}

    metric9 = OtherDummyMetric(expected_value=88)
    metric9.value = 88
    metric9.diagnostic = ""
    metric9.tags = {"domain": "Data Science", "project": "ML Pipeline"}

    metric10 = DummyMetric(expected_value=55)
    metric10.value = 55
    metric10.diagnostic = "⚠ Training data quality concerns"
    metric10.tags = {"domain": "Data Science", "project": "Recommendation Engine"}

    # Create some ungrouped metrics
    metric11 = DummyMetric(expected_value=70)
    metric11.value = 70
    metric11.diagnostic = ""
    metric11.tags = {}  # No tags

    all_metrics = [
        metric1,
        metric2,
        metric3,
        metric4,
        metric5,
        metric6,
        metric7,
        metric8,
        metric9,
        metric10,
        metric11,
    ]
    direct_names = {"dummy", "other_metric"}

    # Generate HTML
    output_file = tmp_path / "metrics_report.html"
    materializer = HTMLMaterializer(
        output_path=output_file,
        group_tag_1="domain",
        group_tag_2="project",
        include_indirect=False,
    )
    materializer.materialize(all_metrics, direct_names)

    # Verify file was created
    assert output_file.exists()

    # Read content for basic validation
    content = output_file.read_text()

    # Verify all domains are present
    assert "Analytics" in content
    assert "Engineering" in content
    assert "Data Science" in content
    assert "Ungrouped" in content

    # Verify all projects are present
    assert "Customer Insights" in content
    assert "Sales Dashboard" in content
    assert "Core Platform" in content
    assert "Mobile App" in content
    assert "ML Pipeline" in content
    assert "Recommendation Engine" in content

    # Verify diagnostic styling
    assert "table-success" in content
    assert "table-warning" in content
    assert "table-danger" in content

    # Print the file path so it can be opened
    print(f"\n\n📊 HTML Report Generated: {output_file}")
    print(f"Open in browser: file://{output_file}\n")

    # Return the path for manual inspection
    return output_file


def test_sqlalchemy_materializer(tmp_path):
    """Test SQLAlchemy materializer writes metrics to database."""
    metric = DummyMetric(expected_value=42)
    metric.value = 42
    metric.tags = {"domain": "Analytics"}

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
    )
    materializer.materialize([metric], {"dummy"})

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
    """Test SQLAlchemy materializer with multiple metrics."""
    from conftest import OtherDummyMetric

    metric1 = DummyMetric(expected_value=42)
    metric1.value = 42

    metric2 = OtherDummyMetric(expected_value=100)
    metric2.value = 100

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
    )
    materializer.materialize([metric1, metric2], {"dummy", "other_metric"})

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 2
    names = {row[0] for row in rows}
    assert names == {"dummy", "other_metric"}


def test_sqlalchemy_materializer_appends_rows(tmp_path):
    """Test that successive materializations append rows."""
    metric = DummyMetric(expected_value=42)
    metric.value = 42

    db_path = tmp_path / "metrics.db"
    url = f"sqlite:///{db_path}"
    materializer = SQLAlchemyMaterializer(connection_url=url)

    # Materialize twice
    materializer.materialize([metric], {"dummy"})
    materializer.materialize([metric], {"dummy"})

    engine = create_engine(url)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 2


def test_sqlalchemy_materializer_custom_table_name(tmp_path):
    """Test SQLAlchemy materializer with custom table name."""
    metric = DummyMetric(expected_value=42)
    metric.value = 42

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
        table_name="checkup_results",
    )
    materializer.materialize([metric], {"dummy"})

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM checkup_results")).fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "dummy"


def test_sqlalchemy_materializer_filters_indirect(tmp_path):
    """Test SQLAlchemy materializer filtering of indirect metrics."""
    from conftest import IndirectDummyMetric

    direct_metric = DummyMetric(expected_value=42)
    direct_metric.value = 42

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_metric.value = 100

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
    )
    materializer.materialize([direct_metric, indirect_metric], {"dummy"})

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "dummy"


def test_sqlalchemy_materializer_includes_indirect(tmp_path):
    """Test SQLAlchemy materializer including indirect metrics."""
    from conftest import IndirectDummyMetric

    direct_metric = DummyMetric(expected_value=42)
    direct_metric.value = 42

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_metric.value = 100

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
        include_indirect=True,
    )
    materializer.materialize([direct_metric, indirect_metric], {"dummy"})

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM metrics")).fetchall()

    assert len(rows) == 2
    names = {row[0] for row in rows}
    assert names == {"dummy", "indirect"}


def test_sqlalchemy_materializer_none_value(tmp_path):
    """Test SQLAlchemy materializer handles None values."""
    metric = DummyMetric(expected_value=42)
    # value is None (not calculated)
    metric.tags = {}

    db_path = tmp_path / "metrics.db"
    materializer = SQLAlchemyMaterializer(
        connection_url=f"sqlite:///{db_path}",
    )
    materializer.materialize([metric], {"dummy"})

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
