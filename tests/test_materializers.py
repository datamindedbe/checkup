"""Tests for materializers."""
import sys
from io import StringIO

import pytest

from checkup.materializers import ConsoleMaterializer, CSVMaterializer, Materializer
from conftest import DummyMetric


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

    materializer = ConsoleMaterializer()
    materializer.materialize([metric])

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
    materializer.materialize([metric])

    # Read and verify CSV content
    content = output_file.read_text()
    lines = content.strip().split("\n")

    # Check header
    assert lines[0] == "name,value,unit,description"

    # Check data row
    assert "dummy" in lines[1]
    assert "42" in lines[1]
    assert "count" in lines[1]


def test_csv_materializer_multiple_metrics(tmp_path):
    """Test CSV materializer with multiple metrics."""
    metric1 = DummyMetric(expected_value=42)
    metric1.value = 42

    metric2 = DummyMetric(expected_value=100, name="other_metric")
    metric2.value = 100

    output_file = tmp_path / "metrics.csv"
    materializer = CSVMaterializer(output_path=output_file)
    materializer.materialize([metric1, metric2])

    content = output_file.read_text()
    lines = content.strip().split("\n")

    assert len(lines) == 3  # Header + 2 data rows
    assert "dummy" in lines[1]
    assert "other_metric" in lines[2]


def test_materializer_filters_indirect_by_default():
    """Test that materializers filter out indirect metrics by default."""
    direct_metric = DummyMetric(expected_value=42, is_direct=True)
    direct_metric.value = 42

    indirect_metric = DummyMetric(expected_value=100, name="indirect", is_direct=False)
    indirect_metric.value = 100

    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    materializer = ConsoleMaterializer()
    materializer.materialize([direct_metric, indirect_metric])

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    assert "dummy" in output  # Direct metric included
    assert "indirect" not in output  # Indirect metric filtered out


def test_materializer_includes_indirect_when_configured():
    """Test that materializers can include indirect metrics."""
    direct_metric = DummyMetric(expected_value=42, is_direct=True)
    direct_metric.value = 42

    indirect_metric = DummyMetric(expected_value=100, name="indirect", is_direct=False)
    indirect_metric.value = 100

    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    materializer = ConsoleMaterializer(include_indirect=True)
    materializer.materialize([direct_metric, indirect_metric])

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    assert "dummy" in output  # Direct metric included
    assert "indirect" in output  # Indirect metric also included


def test_csv_materializer_filters_indirect(tmp_path):
    """Test CSV materializer filtering of indirect metrics."""
    direct_metric = DummyMetric(expected_value=42, is_direct=True)
    direct_metric.value = 42

    indirect_metric = DummyMetric(expected_value=100, name="indirect", is_direct=False)
    indirect_metric.value = 100

    output_file = tmp_path / "metrics.csv"

    # Default: filter indirect
    materializer = CSVMaterializer(output_path=output_file)
    materializer.materialize([direct_metric, indirect_metric])

    content = output_file.read_text()
    lines = content.strip().split("\n")

    assert len(lines) == 2  # Header + 1 direct metric
    assert "dummy" in lines[1]
    assert "indirect" not in content


def test_csv_materializer_includes_indirect(tmp_path):
    """Test CSV materializer including indirect metrics."""
    direct_metric = DummyMetric(expected_value=42, is_direct=True)
    direct_metric.value = 42

    indirect_metric = DummyMetric(expected_value=100, name="indirect", is_direct=False)
    indirect_metric.value = 100

    output_file = tmp_path / "metrics.csv"

    # With include_indirect=True
    materializer = CSVMaterializer(output_path=output_file, include_indirect=True)
    materializer.materialize([direct_metric, indirect_metric])

    content = output_file.read_text()
    lines = content.strip().split("\n")

    assert len(lines) == 3  # Header + 2 metrics
    assert "dummy" in content
    assert "indirect" in content
