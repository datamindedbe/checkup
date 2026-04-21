"""
Tests for plugin registry and discovery.
"""

from typing import ClassVar
from unittest.mock import MagicMock, patch

from checkup.metric import Metric
from checkup.provider import Provider
from checkup.registry.discovery import PluginRegistry
from checkup.types import Context


class MockGitProvider(Provider):
    name: ClassVar[str] = "git"

    def provide(self) -> dict:
        return {}


class MockDbtProvider(Provider):
    name: ClassVar[str] = "dbt"

    def provide(self) -> dict:
        return {}


class MetricRequiringGit(Metric):
    name: ClassVar[str] = "git_metric"
    description: ClassVar[str] = "Requires git"
    unit: ClassVar[str] = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [MockGitProvider]

    def calculate(self, _context: Context, _metrics: dict) -> None:
        self.value = 1


class MetricRequiringDbt(Metric):
    name: ClassVar[str] = "dbt_metric"
    description: ClassVar[str] = "Requires dbt"
    unit: ClassVar[str] = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [MockDbtProvider]

    def calculate(self, _context: Context, _metrics: dict) -> None:
        self.value = 1


class MetricRequiringBoth(Metric):
    name: ClassVar[str] = "both_metric"
    description: ClassVar[str] = "Requires git and dbt"
    unit: ClassVar[str] = "count"

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [MockGitProvider, MockDbtProvider]

    def calculate(self, _context: Context, _metrics: dict) -> None:
        self.value = 1


class StandaloneMetric(Metric):
    name: ClassVar[str] = "standalone"
    description: ClassVar[str] = "No providers required"
    unit: ClassVar[str] = "count"

    def calculate(self, _context: Context, _metrics: dict) -> None:
        self.value = 1


class TestCompatibleMetricFiltering:
    def test_metric_included_when_required_provider_selected(self):
        registry = PluginRegistry()
        registry._metrics = {
            "git_metric": MetricRequiringGit,
            "dbt_metric": MetricRequiringDbt,
        }

        compatible = registry.list_compatible_metric_names(["git"])

        assert "git_metric" in compatible
        assert "dbt_metric" not in compatible

    def test_metric_excluded_when_required_provider_missing(self):
        registry = PluginRegistry()
        registry._metrics = {
            "git_metric": MetricRequiringGit,
        }

        compatible = registry.list_compatible_metric_names(["dbt"])

        assert "git_metric" not in compatible

    def test_metric_requiring_multiple_providers_needs_all(self):
        registry = PluginRegistry()
        registry._metrics = {
            "both_metric": MetricRequiringBoth,
        }

        # Only git selected - not enough
        compatible = registry.list_compatible_metric_names(["git"])
        assert "both_metric" not in compatible

        # Both selected - now compatible
        compatible = registry.list_compatible_metric_names(["git", "dbt"])
        assert "both_metric" in compatible

    def test_standalone_metrics_always_compatible(self):
        registry = PluginRegistry()
        registry._metrics = {
            "standalone": StandaloneMetric,
        }

        # No providers selected
        compatible = registry.list_compatible_metric_names([])
        assert "standalone" in compatible

        # Some providers selected
        compatible = registry.list_compatible_metric_names(["git"])
        assert "standalone" in compatible


class TestRegistryListing:
    def test_list_provider_names_without_loading(self):
        """Listing names should not import any modules."""
        registry = PluginRegistry()

        with patch("checkup.registry.discovery.entry_points") as mock_eps:
            mock_ep = MagicMock()
            mock_ep.name = "git"
            mock_eps.return_value = [mock_ep]

            names = registry.list_provider_names()

            assert names == ["git"]
            mock_ep.load.assert_not_called()

    def test_list_metric_names_without_loading(self):
        registry = PluginRegistry()

        with patch("checkup.registry.discovery.entry_points") as mock_eps:
            mock_ep = MagicMock()
            mock_ep.name = "git_days_since_last_update"
            mock_eps.return_value = [mock_ep]

            names = registry.list_metric_names()

            assert names == ["git_days_since_last_update"]
            mock_ep.load.assert_not_called()
