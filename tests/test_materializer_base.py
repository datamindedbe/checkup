import pytest
from fixtures import DummyMetric, IndirectDummyMetric, capture_output

from checkup.materializers import ConsoleMaterializer, Materializer


def test_materializer_is_abstract():
    """Test that Materializer cannot be instantiated."""
    with pytest.raises(TypeError):
        Materializer()


def test_materializer_filters_indirect_by_default():
    """Test that materializers filter out indirect metrics by default."""
    direct_metric = DummyMetric(expected_value=42)
    direct_measurement = direct_metric.measure(value=42)

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_measurement = indirect_metric.measure(value=100)

    # Only "dummy" is direct, "indirect" is not
    output = capture_output(
        ConsoleMaterializer(group_tags=["domain", "project"]),
        [direct_measurement, indirect_measurement],
        {"dummy"},
    )

    assert "dummy" in output  # Direct metric included
    assert "indirect" not in output  # Indirect metric filtered out


def test_materializer_includes_indirect_when_configured():
    """Test that materializers can include indirect metrics."""
    direct_metric = DummyMetric(expected_value=42)
    direct_measurement = direct_metric.measure(value=42)

    indirect_metric = IndirectDummyMetric(expected_value=100)
    indirect_measurement = indirect_metric.measure(value=100)

    output = capture_output(
        ConsoleMaterializer(include_indirect=True, group_tags=["domain", "project"]),
        [direct_measurement, indirect_measurement],
        {"dummy"},
    )

    assert "dummy" in output  # Direct metric included
    assert "indirect" in output  # Indirect metric also included


def test_materializer_rejects_unknown_column():
    """
    Column names are validated against the known table columns.
    """

    with pytest.raises(ValueError):
        ConsoleMaterializer(columns=["nope"])
