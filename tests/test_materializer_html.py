from fixtures import DummyMetric, IndirectDummyMetric, OtherDummyMetric

from checkup.materializers import HTMLMaterializer


def test_html_materializer(tmp_path):
    """Test HTML materializer with hierarchical grouping."""
    # Create measurements with tags
    metric1 = DummyMetric(expected_value=42)
    measurement1 = metric1.measure(
        value=42, tags={"domain": "Analytics", "project": "Project A"}
    )

    metric2 = DummyMetric(expected_value=100)
    measurement2 = metric2.measure(
        value=100, tags={"domain": "Analytics", "project": "Project B"}
    )

    metric3 = DummyMetric(expected_value=75)
    measurement3 = metric3.measure(
        value=75, tags={"domain": "Engineering", "project": "Project C"}
    )

    output_file = tmp_path / "metrics.html"
    materializer = HTMLMaterializer(
        output_path=output_file, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([measurement1, measurement2, measurement3], {"dummy"})

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
    # Create measurements with different diagnostics
    metric1 = DummyMetric(expected_value=42)
    measurement1 = metric1.measure(
        value=42,
        diagnostic="✅ All good",
        tags={"domain": "Test", "project": "TestProject"},
    )

    metric2 = DummyMetric(expected_value=100)
    measurement2 = metric2.measure(
        value=100,
        diagnostic="⚠ Warning: something to check",
        tags={"domain": "Test", "project": "TestProject"},
    )

    output_file = tmp_path / "metrics.html"
    materializer = HTMLMaterializer(
        output_path=output_file, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([measurement1, measurement2], {"dummy"})

    content = output_file.read_text()

    # Check for diagnostic color classes
    assert "table-success" in content
    assert "table-warning" in content

    # Check diagnostic text is present
    assert "All good" in content
    assert "Warning" in content


def test_html_materializer_ungrouped_metrics(tmp_path):
    """Test HTML materializer with measurements missing tags."""
    # Create measurement without tags
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=42, tags={})

    output_file = tmp_path / "metrics.html"
    materializer = HTMLMaterializer(
        output_path=output_file, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([measurement], {"dummy"})

    content = output_file.read_text()

    # Should default to "Ungrouped"
    assert "Ungrouped" in content
    assert "dummy" in content


def test_html_materializer_filters_indirect(tmp_path):
    """Test HTML materializer filtering of indirect metrics."""
    direct_metric = DummyMetric(expected_value=42)
    direct_measurement = direct_metric.measure(
        value=42, tags={"domain": "Test", "project": "TestProject"}
    )

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_measurement = indirect_metric.measure(
        value=100, tags={"domain": "Test", "project": "TestProject"}
    )

    output_file = tmp_path / "metrics.html"

    # Default: filter indirect
    materializer = HTMLMaterializer(
        output_path=output_file, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([direct_measurement, indirect_measurement], {"dummy"})

    content = output_file.read_text()

    # Only direct metric should be present
    assert "dummy" in content
    assert "indirect" not in content


def test_html_materializer_escape_html(tmp_path):
    """Test that HTML special characters are escaped."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(
        value="<script>alert('xss')</script>",
        diagnostic="Test & verify <tags>",
        tags={"domain": "Test & Dev", "project": "Project <A>"},
    )

    output_file = tmp_path / "metrics.html"
    materializer = HTMLMaterializer(
        output_path=output_file, group_tag_1="domain", group_tag_2="project"
    )
    materializer.materialize([measurement], {"dummy"})

    content = output_file.read_text()

    # Check that special characters are escaped
    assert "&lt;script&gt;" in content
    assert "&amp;" in content
    assert "<script>alert" not in content  # Raw script should not be present


def test_html_materializer_end_to_end(tmp_path):
    """End-to-end test with multiple measurements grouped by domain and project.

    This test creates a realistic scenario with multiple domains and projects,
    generates the HTML, and opens it for visual inspection.
    """
    # Create measurements for Analytics domain
    metric1 = DummyMetric(expected_value=42)
    measurement1 = metric1.measure(
        value=42,
        diagnostic="✅ Good coverage",
        tags={"domain": "Analytics", "project": "Customer Insights"},
    )

    metric2 = OtherDummyMetric(expected_value=85)
    measurement2 = metric2.measure(
        value=85,
        diagnostic="",
        tags={"domain": "Analytics", "project": "Customer Insights"},
    )

    metric3 = DummyMetric(expected_value=100)
    measurement3 = metric3.measure(
        value=100,
        diagnostic="✅ Excellent",
        tags={"domain": "Analytics", "project": "Sales Dashboard"},
    )

    metric4 = OtherDummyMetric(expected_value=60)
    measurement4 = metric4.measure(
        value=60,
        diagnostic="⚠ Below target",
        tags={"domain": "Analytics", "project": "Sales Dashboard"},
    )

    # Create measurements for Engineering domain
    metric5 = DummyMetric(expected_value=95)
    measurement5 = metric5.measure(
        value=95,
        diagnostic="✅ Strong test coverage",
        tags={"domain": "Engineering", "project": "Core Platform"},
    )

    metric6 = OtherDummyMetric(expected_value=45)
    measurement6 = metric6.measure(
        value=45,
        diagnostic="❌ Critical - needs attention",
        tags={"domain": "Engineering", "project": "Core Platform"},
    )

    metric7 = DummyMetric(expected_value=78)
    measurement7 = metric7.measure(
        value=78, diagnostic="", tags={"domain": "Engineering", "project": "Mobile App"}
    )

    # Create measurements for Data Science domain
    metric8 = DummyMetric(expected_value=92)
    measurement8 = metric8.measure(
        value=92,
        diagnostic="✅ Model accuracy within range",
        tags={"domain": "Data Science", "project": "ML Pipeline"},
    )

    metric9 = OtherDummyMetric(expected_value=88)
    measurement9 = metric9.measure(
        value=88,
        diagnostic="",
        tags={"domain": "Data Science", "project": "ML Pipeline"},
    )

    metric10 = DummyMetric(expected_value=55)
    measurement10 = metric10.measure(
        value=55,
        diagnostic="⚠ Training data quality concerns",
        tags={"domain": "Data Science", "project": "Recommendation Engine"},
    )

    # Create some ungrouped measurements
    metric11 = DummyMetric(expected_value=70)
    measurement11 = metric11.measure(value=70, diagnostic="", tags={})

    all_measurements = [
        measurement1,
        measurement2,
        measurement3,
        measurement4,
        measurement5,
        measurement6,
        measurement7,
        measurement8,
        measurement9,
        measurement10,
        measurement11,
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
    materializer.materialize(all_measurements, direct_names)

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
