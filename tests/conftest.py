import pytest
from fixtures import DependentDummyMetric, DummyMetric


@pytest.fixture
def dummy_metric():
    """Create a DummyMetric instance with default value."""
    return DummyMetric()


@pytest.fixture
def dummy_measurement_with_value():
    """Create a Measurement from a DummyMetric with value already calculated."""
    metric = DummyMetric(expected_value=10)
    return metric.calculate(context={}, measurements={})


@pytest.fixture
def dependent_metric():
    """Create a DependentDummyMetric instance."""
    return DependentDummyMetric()


@pytest.fixture
def empty_context():
    """Create an empty context dict."""
    return {}
