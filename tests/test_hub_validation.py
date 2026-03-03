"""Tests for provider validation in CheckHub."""

from typing import Any, ClassVar

from checkup.metric import Metric
from checkup.provider import Provider
from checkup.types import Context
from checkup.validators import validate_providers


class RequiredProvider(Provider):
    """Provider that metrics require."""

    name: ClassVar[str] = "required"

    def provide(self) -> dict[str, Any]:
        return {"data": "value"}


class OtherProvider(Provider):
    """Another provider."""

    name: ClassVar[str] = "other"

    def provide(self) -> dict[str, Any]:
        return {"other": "data"}


class MetricWithProvider(Metric):
    """Metric that requires a provider."""

    name: ClassVar[str] = "needs_provider"
    description: ClassVar[str] = "Needs RequiredProvider"
    unit: ClassVar[str] = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [RequiredProvider]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = 1


class TestProviderValidation:
    """Tests for validate_providers method."""

    def test_validation_passes_with_required_providers(self):
        """Test validation passes when all required providers present."""
        validate_providers(
            metrics=[MetricWithProvider],
            provider_sets=[[RequiredProvider()]],
        )
        # No exception raised

    def test_validation_warns_with_missing_provider(self, caplog):
        """Test validation warns when required provider missing."""
        with caplog.at_level("WARNING"):
            validate_providers(
                metrics=[MetricWithProvider],
                provider_sets=[[OtherProvider()]],
            )

        assert "required" in caplog.text.lower()

    def test_validation_warns_with_empty_provider_set(self, caplog):
        """Test validation warns with empty provider set."""
        with caplog.at_level("WARNING"):
            validate_providers(
                metrics=[MetricWithProvider],
                provider_sets=[[]],
            )

        assert "required" in caplog.text.lower()

    def test_validation_warns_for_each_provider_set(self, caplog):
        """Test validation warns for each provider set with missing providers."""
        with caplog.at_level("WARNING"):
            validate_providers(
                metrics=[MetricWithProvider],
                provider_sets=[
                    [RequiredProvider()],  # OK
                    [OtherProvider()],  # Missing
                ],
            )

        assert "1" in caplog.text  # Provider set index

    def test_validation_passes_with_no_required_providers(self):
        """Test validation passes when metrics need no providers."""
        from fixtures import DummyMetric

        validate_providers(
            metrics=[DummyMetric],
            provider_sets=[[]],
        )
        # No exception raised
