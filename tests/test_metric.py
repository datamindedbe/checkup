"""Tests for Metric ABC and test fixtures."""

from fixtures import (
    DependentDummyMetric,
    DummyMetric,
    DummyProvider,
    ProviderDummyMetric,
)
from pydantic import BaseModel

from checkup.measurement import Measurements
from checkup.metric import Metric


class TestDummyMetricInstantiation:
    def test_with_explicit_value(self):
        """Test that DummyMetric can be instantiated with config."""
        metric = DummyMetric(expected_value=42)

        assert metric.name == "dummy"
        assert metric.description == "Test metric"
        assert metric.unit == "count"
        assert metric.expected_value == 42

    def test_with_default_value(self):
        """Test that DummyMetric uses default expected_value."""
        metric = DummyMetric()

        assert metric.expected_value == 42


class TestDummyMetricCalculation:
    def test_returns_measurement(self, empty_context):
        """Test that DummyMetric.calculate() returns a Measurement."""
        metric = DummyMetric(expected_value=100)

        measurement = metric.calculate(
            context=empty_context, measurements=Measurements()
        )

        assert measurement.value == 100
        assert measurement.metric.name == "dummy"

    def test_uses_fixture(self, dummy_metric, empty_context):
        """Test calculate using pytest fixtures."""
        measurement = dummy_metric.calculate(
            context=empty_context, measurements=Measurements()
        )

        assert measurement.value == 42


class TestMetricBaseClass:
    def test_default_depends_on(self):
        """Test that Metric base class depends_on returns empty list."""
        assert DummyMetric.depends_on() == []

    def test_default_providers(self):
        """Test that Metric base class providers returns empty list."""
        assert DummyMetric.providers() == []

    def test_is_pydantic_model(self):
        """Test that Metric is a proper Pydantic model."""
        assert issubclass(Metric, BaseModel)

    def test_pydantic_model_dump(self):
        """Test that we can use Pydantic features."""
        metric = DummyMetric(expected_value=50)

        data = metric.model_dump()
        assert data["expected_value"] == 50
        assert data["name"] == "dummy"


class TestDependentDummyMetric:
    def test_depends_on(self):
        """Test that DependentDummyMetric declares dependencies."""
        deps = DependentDummyMetric.depends_on()

        assert deps == [DummyMetric]

    def test_calculate(self, dummy_measurement_with_value):
        """Test that DependentDummyMetric uses dependency value."""
        dependent = DependentDummyMetric()
        calculated = Measurements({DummyMetric: [dummy_measurement_with_value]})
        measurement = dependent.calculate(context={}, measurements=calculated)

        assert measurement.value == 20  # 10 * 2

    def test_calculate_custom_base(self, empty_context):
        """Test calculation with custom base value."""
        base_metric = DummyMetric(expected_value=25)
        base_measurement = base_metric.calculate(
            context=empty_context, measurements=Measurements()
        )

        dependent = DependentDummyMetric()
        calculated = Measurements({DummyMetric: [base_measurement]})
        measurement = dependent.calculate(
            context=empty_context, measurements=calculated
        )

        assert measurement.value == 50  # 25 * 2


class TestProviderSystem:
    def test_dummy_provider_adds_data(self):
        """Test DummyProvider adds data."""
        provider = DummyProvider()
        result = provider.provide()
        assert result == {"data": 100}

    def test_dummy_provider_with_custom_data(self):
        """Test DummyProvider with custom data."""
        provider = DummyProvider(data=42)
        result = provider.provide()
        assert result == {"data": 42}

    def test_provider_dummy_metric_has_provider(self):
        """Test that ProviderDummyMetric declares providers."""
        providers = ProviderDummyMetric.providers()

        assert providers == [DummyProvider]

    def test_provider_dummy_metric_calculate(self):
        """Test that ProviderDummyMetric uses context from provider."""
        # Build context with namespaced provider data
        provider = DummyProvider()
        context = {DummyProvider.name: provider.provide()}

        metric = ProviderDummyMetric()
        measurement = metric.calculate(context=context, measurements=Measurements())

        assert measurement.value == 100
