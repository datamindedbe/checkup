"""Tests for CheckHub execution with instance-based providers."""

from typing import Any, ClassVar

from checkup.hub import CheckHub
from checkup.metric import Metric
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

    name: ClassVar[str] = "data_metric"
    description: ClassVar[str] = "Uses data provider"
    unit: ClassVar[str] = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [DataProvider]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = context[DataProvider.name]["value"]


class TestHubExecution:
    """Tests for measure() with new provider system."""

    def test_measure_with_single_provider_set(self):
        """Test measuring with single provider set."""
        result = (
            CheckHub()
            .with_metrics([DataMetric])
            .with_providers([[DataProvider(value=42)]])
            .measure()
        )

        assert len(result.metrics) == 1
        assert result.metrics[0].value == 42

    def test_measure_with_multiple_provider_sets(self):
        """Test measuring across multiple provider sets."""
        result = (
            CheckHub()
            .with_metrics([DataMetric])
            .with_providers([
                [DataProvider(value=10)],
                [DataProvider(value=20)],
                [DataProvider(value=30)],
            ])
            .measure()
        )

        assert len(result.metrics) == 3
        values = {m.value for m in result.metrics}
        assert values == {10, 20, 30}

    def test_measure_with_tag_provider(self):
        """Test that TagProvider merges into metric tags."""
        result = (
            CheckHub()
            .with_metrics([DataMetric])
            .with_providers([
                [DataProvider(value=42), TagProvider(env="prod", team="data")],
            ])
            .measure()
        )

        metric = result.metrics[0]
        assert metric.tags["env"] == "prod"
        assert metric.tags["team"] == "data"

    def test_measure_validates_providers(self):
        """Test that measure() validates providers before running."""
        import pytest

        with pytest.raises(ValueError) as exc_info:
            CheckHub().with_metrics([DataMetric]).with_providers([[]]).measure()

        assert "data" in str(exc_info.value).lower()

    def test_measure_with_empty_provider_sets_and_no_requirements(self):
        """Test measuring without providers when none required."""
        from conftest import DummyMetric

        result = CheckHub().with_metrics([DummyMetric]).measure()

        assert len(result.metrics) == 1
        assert result.metrics[0].value == 42
