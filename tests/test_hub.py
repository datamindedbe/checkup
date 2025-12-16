"""Tests for CheckHub main orchestration."""
import sys
from io import StringIO
from pathlib import Path

from checkup.hub import CheckHub, MeasurementResult
from checkup.materializers import ConsoleMaterializer
from conftest import (
    DependentDummyMetric,
    DummyMetric,
    Level3Metric,
    ProviderDummyMetric,
)


def test_checkhub_creation():
    """Test creating a CheckHub instance."""
    hub = CheckHub()

    assert hub is not None


def test_checkhub_with_metrics():
    """Test registering metrics with CheckHub."""
    hub = CheckHub().with_metrics([DummyMetric])

    assert isinstance(hub, CheckHub)


def test_measurement_result_creation():
    """Test creating a MeasurementResult."""
    metric = DummyMetric(expected_value=42)
    result = MeasurementResult(metrics=[metric])

    assert len(result.metrics) == 1
    assert result.metrics[0] == metric


def test_measurement_result_with_errors():
    """Test MeasurementResult can hold errors."""
    metric = DummyMetric(expected_value=42)
    metric.value = 42

    errors = [({"path": "/bad/path"}, ValueError("Path not found"))]

    result = MeasurementResult(metrics=[metric], errors=errors)

    assert len(result.metrics) == 1
    assert len(result.errors) == 1
    assert result.errors[0][0] == {"path": "/bad/path"}


def test_measurement_result_errors_default_empty():
    """Test MeasurementResult.errors defaults to empty list."""
    metric = DummyMetric(expected_value=42)
    result = MeasurementResult(metrics=[metric])

    assert result.errors == []


def test_checkhub_measure_simple():
    """Test measuring a single metric with no dependencies."""
    result = CheckHub().with_metrics([DummyMetric]).measure()

    assert len(result.metrics) == 1
    assert result.metrics[0].name == "dummy"
    assert result.metrics[0].value == 42


def test_checkhub_measure_with_dependencies():
    """Test measuring metrics with dependencies.

    DependentDummyMetric depends on DummyMetric and doubles its value.
    """
    result = CheckHub().with_metrics([DependentDummyMetric]).measure()

    # All metrics returned (both direct and indirect)
    assert len(result.metrics) == 2

    # Check direct_metric_names
    assert "dummy" not in result.direct_metric_names
    assert "dependent_dummy" in result.direct_metric_names

    metrics_by_name = {m.name: m for m in result.metrics}
    assert metrics_by_name["dependent_dummy"].value == 84  # 42 * 2


def test_checkhub_measure_deep_dependency_chain():
    """Test measuring metrics with deep dependency chain.

    DummyMetric(42) → DependentDummyMetric(84) → Level2Metric(94) → Level3Metric(8836)
    """
    result = CheckHub().with_metrics([Level3Metric]).measure()

    # All 4 metrics returned
    assert len(result.metrics) == 4

    # Only Level3Metric is direct
    assert result.direct_metric_names == {"level3"}

    metrics_by_name = {m.name: m for m in result.metrics}
    assert metrics_by_name["level3"].value == 8836  # (84 + 10) ** 2 = 94 ** 2


def test_checkhub_measure_with_provider():
    """Test measuring a metric that uses a provider.

    ProviderDummyMetric requires DummyProvider.
    """
    from conftest import DummyProvider

    result = (
        CheckHub()
        .with_metrics([ProviderDummyMetric])
        .with_providers([[DummyProvider()]])
        .measure()
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].name == "provider_dummy"
    assert result.metrics[0].value == 100  # Value from dummy_provider


def test_checkhub_measure_with_providers():
    """Test that providers are executed correctly."""
    from conftest import DummyProvider, ProviderDummyMetric

    result = (
        CheckHub()
        .with_metrics([ProviderDummyMetric])
        .with_providers([[DummyProvider()]])
        .measure()
    )

    assert result.metrics[0].value == 100  # Provider works


def test_checkhub_measure_with_config():
    """Test measuring metrics with YAML config."""
    config_path = Path(__file__).parent / "fixtures" / "test_config.yaml"

    result = CheckHub(config_path=config_path).with_metrics([DummyMetric]).measure()

    assert len(result.metrics) == 1
    assert result.metrics[0].value == 200  # From YAML, not default 42


def test_measurement_result_materialize():
    """Test materializing measurement results."""
    captured_output = StringIO()
    sys.stdout = captured_output

    CheckHub().with_metrics([DummyMetric]).measure().materialize(ConsoleMaterializer())

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    assert "dummy" in output




def test_checkhub_measure_multiple_provider_sets():
    """Test measuring metrics across multiple provider sets."""
    from checkup.providers.tags import TagProvider

    result = (
        CheckHub()
        .with_metrics([DummyMetric])
        .with_providers([
            [TagProvider(path="/repo1")],
            [TagProvider(path="/repo2")],
            [TagProvider(path="/repo3")],
        ])
        .measure()
    )

    assert len(result.metrics) == 3
    paths = {m.tags["path"] for m in result.metrics}
    assert paths == {"/repo1", "/repo2", "/repo3"}


def test_checkhub_measure_parallel():
    """Test parallel execution with max_workers."""
    from checkup.providers.tags import TagProvider

    result = (
        CheckHub()
        .with_metrics([DummyMetric])
        .with_providers([[TagProvider(path=f"/repo{i}")] for i in range(10)])
        .measure(max_workers=4)
    )

    assert len(result.metrics) == 10


