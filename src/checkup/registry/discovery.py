"""
Plugin discovery via Python entry points.
"""

import logging
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from checkup.materializers import Materializer
    from checkup.metric import Metric
    from checkup.provider import Provider

logger = logging.getLogger(__name__)

# Entry point group names
PROVIDERS_GROUP = "checkup.providers"
METRICS_GROUP = "checkup.metrics"
MATERIALIZERS_GROUP = "checkup.materializers"


class PluginRegistry:
    """
    Registry for discovering and loading checkup plugins.

    Plugins register providers, metrics, and materializers via entry points
    in their pyproject.toml.
    """

    def __init__(self) -> None:
        """
        Initialize the registry.
        """

        self._providers: dict[str, type[Provider]] | None = None
        self._metrics: dict[str, type[Metric]] | None = None
        self._materializers: dict[str, type[Materializer]] | None = None

    def _list_entry_point_names(self, group: str) -> list[str]:
        """
        List entry point names without loading them.
        """

        eps = entry_points(group=group)
        return [ep.name for ep in eps]

    def _load_entry_points(self, group: str) -> dict[str, type]:
        """
        Load all entry points for a group.
        """

        result = {}
        eps = entry_points(group=group)

        for ep in eps:
            try:
                cls = ep.load()
                result[ep.name] = cls
                logger.debug("Loaded %s: %s", group, ep.name)
            except Exception as e:
                logger.warning("Failed to load %s '%s': %s", group, ep.name, e)

        return result

    @property
    def providers(self) -> dict[str, type["Provider"]]:
        """
        Get all registered providers.
        """

        if self._providers is None:
            self._providers = self._load_entry_points(PROVIDERS_GROUP)

        return self._providers

    @property
    def metrics(self) -> dict[str, type["Metric"]]:
        """
        Get all registered metrics.
        """

        if self._metrics is None:
            self._metrics = self._load_entry_points(METRICS_GROUP)

        return self._metrics

    @property
    def materializers(self) -> dict[str, type["Materializer"]]:
        """
        Get all registered materializers.
        """

        if self._materializers is None:
            self._materializers = self._load_entry_points(MATERIALIZERS_GROUP)

        return self._materializers

    def get_provider(self, name: str) -> type["Provider"] | None:
        """
        Get a provider class by name.
        """

        return self.providers.get(name)

    def get_metric(self, name: str) -> type["Metric"] | None:
        """
        Get a metric class by name.
        """

        return self.metrics.get(name)

    def get_materializer(self, name: str) -> type["Materializer"] | None:
        """
        Get a materializer class by name.
        """

        return self.materializers.get(name)

    def list_provider_names(self) -> list[str]:
        """
        List available provider names without loading them.
        """

        return self._list_entry_point_names(PROVIDERS_GROUP)

    def list_metric_names(self) -> list[str]:
        """
        List available metric names without loading them.
        """

        return self._list_entry_point_names(METRICS_GROUP)

    def list_materializer_names(self) -> list[str]:
        """
        List available materializer names without loading them.
        """

        return self._list_entry_point_names(MATERIALIZERS_GROUP)

    def list_compatible_metric_names(self, provider_names: list[str]) -> list[str]:
        """
        List metric names compatible with the given providers.

        A metric is compatible if all its required providers (from providers() method)
        are in the selected provider list. Metrics with no required providers are
        always compatible.
        """

        provider_set = set(provider_names)
        compatible = []

        for name, metric_cls in self.metrics.items():
            required_providers = metric_cls.providers()

            if not required_providers:
                # No provider requirements - always compatible
                compatible.append(name)
                continue

            # Check if all required providers are selected
            required_names = {p.name for p in required_providers}
            if required_names <= provider_set:
                compatible.append(name)

        return compatible

    def clear_cache(self) -> None:
        """
        Clear cached plugins (useful for testing).
        """

        self._providers = None
        self._metrics = None
        self._materializers = None


# Global registry instance
_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    """
    Get the global plugin registry.
    """

    global _registry
    if _registry is None:
        _registry = PluginRegistry()

    return _registry
