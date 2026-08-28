from fixtures import DummyMetric, IndirectDummyMetric, OtherDummyMetric

from checkup.materializers import CSVMaterializer


def test_csv_materializer(tmp_path):
    """Test CSV file materializer."""
    metric = DummyMetric(expected_value=42)
    measurement = metric.measure(value=42)

    output_file = tmp_path / "metrics.csv"
    materializer = CSVMaterializer(output_path=output_file)
    materializer.materialize([measurement], {"dummy"})

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
    metric1 = DummyMetric(expected_value=42)
    measurement1 = metric1.measure(value=42)

    metric2 = OtherDummyMetric(expected_value=100)
    measurement2 = metric2.measure(value=100)

    output_file = tmp_path / "metrics.csv"
    materializer = CSVMaterializer(output_path=output_file)
    materializer.materialize([measurement1, measurement2], {"dummy", "other_metric"})

    content = output_file.read_text()
    lines = content.strip().split("\n")

    assert len(lines) == 3  # Header + 2 data rows
    assert "dummy" in lines[1]
    assert "other_metric" in lines[2]


def test_csv_materializer_filters_indirect(tmp_path):
    """Test CSV materializer filtering of indirect metrics."""
    direct_metric = DummyMetric(expected_value=42)
    direct_measurement = direct_metric.measure(value=42)

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_measurement = indirect_metric.measure(value=100)

    output_file = tmp_path / "metrics.csv"

    # Default: filter indirect
    materializer = CSVMaterializer(output_path=output_file)
    # Only "dummy" is direct
    materializer.materialize([direct_measurement, indirect_measurement], {"dummy"})

    content = output_file.read_text()
    lines = content.strip().split("\n")

    assert len(lines) == 2  # Header + 1 direct metric
    assert "dummy" in lines[1]
    assert "indirect" not in content


def test_csv_materializer_includes_indirect(tmp_path):
    """Test CSV materializer including indirect metrics."""
    direct_metric = DummyMetric(expected_value=42)
    direct_measurement = direct_metric.measure(value=42)

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_measurement = indirect_metric.measure(value=100)

    output_file = tmp_path / "metrics.csv"

    # With include_indirect=True
    materializer = CSVMaterializer(output_path=output_file, include_indirect=True)
    materializer.materialize([direct_measurement, indirect_measurement], {"dummy"})

    content = output_file.read_text()
    lines = content.strip().split("\n")

    assert len(lines) == 3  # Header + 2 metrics
    assert "dummy" in content
    assert "indirect" in content
