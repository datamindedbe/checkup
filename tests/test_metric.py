"""Tests for Metric ABC and test fixtures."""

from fixtures import (
    DependentDummyMetric,
    DummyMetric,
    DummyProvider,
    ProviderDummyMetric,
)
from pydantic import BaseModel

from checkup.metric import Metric

# =============================================================================
# DummyMetric instantiation tests
# =============================================================================


def test_dummy_metric_with_explicit_value():
    """Test that DummyMetric can be instantiated with config."""
    metric = DummyMetric(expected_value=42)

    assert metric.name == "dummy"
    assert metric.description == "Test metric"
    assert metric.unit == "count"
    assert metric.value is None
    assert metric.expected_value == 42


def test_dummy_metric_with_default_value():
    """Test that DummyMetric uses default expected_value."""
    metric = DummyMetric()

    assert metric.expected_value == 42
    assert metric.value is None


# =============================================================================
# DummyMetric calculation tests
# =============================================================================


def test_dummy_metric_calculate_sets_value(empty_context):
    """Test that DummyMetric.calculate() sets value correctly."""
    metric = DummyMetric(expected_value=100)

    assert metric.value is None

    metric.calculate(context=empty_context, metrics={})

    assert metric.value == 100


def test_dummy_metric_calculate_uses_fixture(dummy_metric, empty_context):
    """Test calculate using pytest fixtures."""
    dummy_metric.calculate(context=empty_context, metrics={})

    assert dummy_metric.value == 42


# =============================================================================
# Metric base class tests
# =============================================================================


def test_metric_default_depends_on():
    """Test that Metric base class depends_on returns empty list."""
    assert DummyMetric.depends_on() == []


def test_metric_default_providers():
    """Test that Metric base class providers returns empty list."""
    assert DummyMetric.providers() == []


def test_metric_is_pydantic_model():
    """Test that Metric is a proper Pydantic model."""
    assert issubclass(Metric, BaseModel)


def test_metric_pydantic_model_dump():
    """Test that we can use Pydantic features."""
    metric = DummyMetric(expected_value=50)

    # ClassVar fields are not included in model_dump, access them directly
    assert metric.name == "dummy"
    assert DummyMetric.name == "dummy"  # Can also access on class

    # Instance fields are in model_dump
    data = metric.model_dump()
    assert data["expected_value"] == 50
    assert data["value"] is None
    assert "name" not in data  # ClassVar not included in dump


# =============================================================================
# DependentDummyMetric tests
# =============================================================================


def test_dependent_metric_depends_on():
    """Test that DependentDummyMetric declares dependencies."""
    deps = DependentDummyMetric.depends_on()

    assert deps == [DummyMetric]


def test_dependent_metric_calculate(dummy_metric_with_value):
    """Test that DependentDummyMetric uses dependency value."""
    dependent = DependentDummyMetric()
    dependent.calculate(context={}, metrics={DummyMetric: dummy_metric_with_value})

    assert dependent.value == 20  # 10 * 2


def test_dependent_metric_calculate_custom_base(empty_context):
    """Test calculation with custom base value."""
    base_metric = DummyMetric(expected_value=25)
    base_metric.calculate(context=empty_context, metrics={})

    dependent = DependentDummyMetric()
    dependent.calculate(context=empty_context, metrics={DummyMetric: base_metric})

    assert dependent.value == 50  # 25 * 2


# =============================================================================
# Provider system tests
# =============================================================================


def test_dummy_provider_adds_data():
    """Test DummyProvider adds data."""
    provider = DummyProvider()
    result = provider.provide()
    assert result == {"data": 100}


def test_dummy_provider_with_custom_data():
    """Test DummyProvider with custom data."""
    provider = DummyProvider(data=42)
    result = provider.provide()
    assert result == {"data": 42}


def test_provider_dummy_metric_has_provider():
    """Test that ProviderDummyMetric declares providers."""
    providers = ProviderDummyMetric.providers()

    assert providers == [DummyProvider]


def test_provider_dummy_metric_calculate():
    """Test that ProviderDummyMetric uses context from provider."""
    # Build context with namespaced provider data
    provider = DummyProvider()
    context = {DummyProvider.name: provider.provide()}

    metric = ProviderDummyMetric()
    metric.calculate(context=context, metrics={})

    assert metric.value == 100
