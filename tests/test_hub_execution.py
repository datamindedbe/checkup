"""Tests for CheckHub execution with instance-based providers."""

from typing import Any, ClassVar

from fixtures import (
    DependentDummyMetric,
    DummyMetric,
    IntegrationBaseMetric,
    IntegrationDerivedMetric,
)

from checkup.hub import CheckHub
from checkup.metric import Measurement, Metric
from checkup.provider import Provider
from checkup.providers.tags import TagProvider
from checkup.types import Context


class DataProvider(Provider):
    """Provider that supplies data."""

    name: ClassVar[str] = "data"

    def __init__(self, value: int = 100):
        self.value = value

    def provide(self) -> dict[str, Any]:
        return {"value": self.value}


class DataMetric(Metric):
    """Metric that uses DataProvider."""

    name: str = "data_metric"
    description: str = "Uses data provider"
    unit: str = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [DataProvider]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        value = context[DataProvider.name]["value"]
        return self.measure(value=value)


class OtherProvider(Provider):
    """Another provider for testing partial provider availability."""

    name: ClassVar[str] = "other"

    def provide(self) -> dict[str, Any]:
        return {"other_value": 999}


class FailingProvider(Provider):
    """Provider that always fails."""

    name: ClassVar[str] = "failing"

    def provide(self) -> dict[str, Any]:
        raise RuntimeError("Provider failed intentionally")


class FailingProviderMetric(Metric):
    """Metric that depends on FailingProvider."""

    name: str = "failing_provider_metric"
    description: str = "Uses failing provider"
    unit: str = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [FailingProvider]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        return self.measure(value=999)


class DependsOnFailingMetric(Metric):
    """Metric that depends on FailingProviderMetric."""

    name: str = "depends_on_failing_metric"
    description: str = "Depends on failing metric"
    unit: str = "count"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [FailingProviderMetric]

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [FailingProvider]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        base_val = self.get_single(measurements, FailingProviderMetric).value
        return self.measure(value=base_val * 2)


class OtherMetric(Metric):
    """Metric that uses OtherProvider."""

    name: str = "other_metric"
    description: str = "Uses other provider"
    unit: str = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [OtherProvider]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        value = context[OtherProvider.name]["other_value"]
        return self.measure(value=value)


class TestHubExecution:
    """Tests for measure() with new provider system."""

    def test_measure_with_single_provider_set(self):
        """Test measuring with single provider set."""
        result = (
            CheckHub()
            .with_metrics([DataMetric()])
            .with_providers([[DataProvider(value=42)]])
            .measure()
        )

        assert len(result.measurements) == 1
        assert result.measurements[0].value == 42

    def test_measure_with_multiple_provider_sets(self):
        """Test measuring across multiple provider sets."""
        result = (
            CheckHub()
            .with_metrics([DataMetric()])
            .with_providers(
                [
                    [DataProvider(value=10)],
                    [DataProvider(value=20)],
                    [DataProvider(value=30)],
                ]
            )
            .measure()
        )

        assert len(result.measurements) == 3
        values = {m.value for m in result.measurements}
        assert values == {10, 20, 30}

    def test_measure_with_tag_provider(self):
        """Test that TagProvider merges into metric tags."""
        result = (
            CheckHub()
            .with_metrics([DataMetric()])
            .with_providers(
                [
                    [DataProvider(value=42), TagProvider(env="prod", team="data")],
                ]
            )
            .measure()
        )

        measurement = result.measurements[0]
        assert measurement.tags["env"] == "prod"
        assert measurement.tags["team"] == "data"

    def test_measure_warns_on_missing_providers(self, caplog):
        """Test that measure() warns when providers are missing."""
        import logging

        with caplog.at_level(logging.WARNING):
            CheckHub().with_metrics([DataMetric()]).with_providers([[]]).measure()

        assert "data" in caplog.text.lower()

    def test_measure_with_empty_provider_sets_and_no_requirements(self):
        """Test measuring without providers when none required."""
        result = CheckHub().with_metrics([DummyMetric()]).measure()

        assert len(result.measurements) == 1
        assert result.measurements[0].value == 42

    def test_measure_skips_only_metrics_with_missing_providers(self, caplog):
        """Test that metrics with available providers are still calculated when others are missing."""
        import logging

        # Request both metrics but only provide DataProvider (not OtherProvider)
        with caplog.at_level(logging.WARNING):
            result = (
                CheckHub()
                .with_metrics([DataMetric(), OtherMetric()])
                .with_providers([[DataProvider(value=42)]])
                .measure()
            )

        # DataMetric should be calculated (has its provider)
        # OtherMetric should be skipped (missing OtherProvider)
        assert len(result.measurements) == 1
        assert result.measurements[0].metric.name == "data_metric"
        assert result.measurements[0].value == 42

        # Warning should be logged for the missing provider
        assert "other" in caplog.text.lower()

    def test_measure_skips_dependent_metrics_when_dependency_skipped(self):
        """When a metric's dependency is skipped due to missing provider, the dependent is also skipped."""
        # IntegrationBaseMetric requires IntegrationProvider
        # IntegrationDerivedMetric depends on IntegrationBaseMetric
        # If we don't provide IntegrationProvider, both should be skipped
        result = (
            CheckHub()
            .with_metrics([IntegrationBaseMetric(), IntegrationDerivedMetric()])
            .with_providers([[]])  # No providers
            .measure()
        )

        # Both metrics should be skipped - no errors should occur
        assert len(result.measurements) == 0
        assert (
            len(result.errors) == 0
        )  # No exceptions from trying to access missing dependency

    def test_failed_provider_metric_has_null_value_with_diagnostic(self):
        """When a provider fails, metrics depending on it have value=None with diagnostic."""
        result = (
            CheckHub()
            .with_metrics([FailingProviderMetric()])
            .with_providers([[FailingProvider()]])
            .measure()
        )

        assert len(result.measurements) == 1
        measurement = result.measurements[0]
        assert measurement.metric.name == "failing_provider_metric"
        assert measurement.value is None
        assert "provider 'failing' failed" in measurement.diagnostic

    def test_failed_provider_does_not_affect_unrelated_metrics(self):
        """When a provider fails, unrelated metrics are still calculated."""
        result = (
            CheckHub()
            .with_metrics([DataMetric(), FailingProviderMetric()])
            .with_providers([[DataProvider(value=42), FailingProvider()]])
            .measure()
        )

        assert len(result.measurements) == 2

        data_measurement = next(
            m for m in result.measurements if m.metric.name == "data_metric"
        )
        assert data_measurement.value == 42

        failing_measurement = next(
            m for m in result.measurements if m.metric.name == "failing_provider_metric"
        )
        assert failing_measurement.value is None
        assert "failed" in failing_measurement.diagnostic

    def test_metric_depending_on_failed_metric_also_fails(self):
        """When a metric fails due to provider failure, dependents also fail."""
        result = (
            CheckHub()
            .with_metrics([FailingProviderMetric(), DependsOnFailingMetric()])
            .with_providers([[FailingProvider()]])
            .measure()
        )

        assert len(result.measurements) == 2

        base_measurement = next(
            m for m in result.measurements if m.metric.name == "failing_provider_metric"
        )
        assert base_measurement.value is None
        assert "provider 'failing' failed" in base_measurement.diagnostic

        dependent_measurement = next(
            m
            for m in result.measurements
            if m.metric.name == "depends_on_failing_metric"
        )
        assert dependent_measurement.value is None
        assert (
            "metric 'FailingProviderMetric' failed" in dependent_measurement.diagnostic
        )

    def test_multiple_instances_of_same_metric_class(self):
        """Test that multiple instances of the same metric class each produce measurements."""

        result = (
            CheckHub()
            .with_metrics(
                [
                    DummyMetric(name="dummy_a", expected_value=10),
                    DummyMetric(name="dummy_b", expected_value=20),
                    DummyMetric(name="dummy_c", expected_value=30),
                ]
            )
            .measure()
        )

        assert len(result.measurements) == 3
        measurements_by_name = {m.metric.name: m for m in result.measurements}
        assert measurements_by_name["dummy_a"].value == 10
        assert measurements_by_name["dummy_b"].value == 20
        assert measurements_by_name["dummy_c"].value == 30

    def test_multiple_instances_dependency_with_get_single_fails(self):
        """Test that get_single raises when multiple instances exist for a dependency."""

        # DependentDummyMetric uses get_single() which should fail with multiple DummyMetric instances
        result = (
            CheckHub()
            .with_metrics(
                [
                    DummyMetric(name="dummy_1", expected_value=5),
                    DummyMetric(name="dummy_2", expected_value=15),
                    DependentDummyMetric(),
                ]
            )
            .measure()
        )

        # The whole provider set fails because get_single() raises during calculation
        assert len(result.errors) == 1
        assert "Expected single measurement for DummyMetric, got 2" in str(
            result.errors[0][1]
        )
