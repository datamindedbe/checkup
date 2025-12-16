"""Tests for provider validation in CheckHub."""

from typing import Any, ClassVar

import pytest

from checkup.hub import CheckHub
from checkup.metric import Metric
from checkup.provider import Provider
from checkup.types import Context


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
    """Tests for _validate_providers method."""

    def test_validation_passes_with_required_providers(self):
        """Test validation passes when all required providers present."""
        hub = CheckHub().with_metrics([MetricWithProvider])
        hub._validate_providers(
            metrics=[MetricWithProvider],
            provider_sets=[[RequiredProvider()]],
        )
        # No exception raised

    def test_validation_fails_with_missing_provider(self):
        """Test validation fails when required provider missing."""
        hub = CheckHub().with_metrics([MetricWithProvider])

        with pytest.raises(ValueError) as exc_info:
            hub._validate_providers(
                metrics=[MetricWithProvider],
                provider_sets=[[OtherProvider()]],
            )

        assert "required" in str(exc_info.value).lower()

    def test_validation_fails_with_empty_provider_set(self):
        """Test validation fails with empty provider set."""
        hub = CheckHub().with_metrics([MetricWithProvider])

        with pytest.raises(ValueError) as exc_info:
            hub._validate_providers(
                metrics=[MetricWithProvider],
                provider_sets=[[]],
            )

        assert "required" in str(exc_info.value).lower()

    def test_validation_checks_all_provider_sets(self):
        """Test validation checks each provider set independently."""
        hub = CheckHub().with_metrics([MetricWithProvider])

        with pytest.raises(ValueError) as exc_info:
            hub._validate_providers(
                metrics=[MetricWithProvider],
                provider_sets=[
                    [RequiredProvider()],  # OK
                    [OtherProvider()],  # Missing
                ],
            )

        assert "1" in str(exc_info.value)  # Provider set index

    def test_validation_passes_with_no_required_providers(self):
        """Test validation passes when metrics need no providers."""
        from conftest import DummyMetric

        hub = CheckHub().with_metrics([DummyMetric])
        hub._validate_providers(
            metrics=[DummyMetric],
            provider_sets=[[]],
        )
        # No exception raised
