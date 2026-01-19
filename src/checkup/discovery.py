"""Plugin discovery via entry points."""

import logging
from importlib.metadata import distributions, entry_points
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from checkup.metric import Metric
    from checkup.provider import Provider

logger = logging.getLogger(__name__)


def discover_metrics() -> dict[str, type["Metric"]]:
    """Discover all registered metrics from installed plugins.

    Returns:
        Dict mapping metric names to their classes
    """
    metrics: dict[str, type["Metric"]] = {}
    eps = entry_points(group="checkup.metrics")
    for ep in eps:
        try:
            metrics[ep.name] = ep.load()
            logger.debug("Discovered metric: %s", ep.name)
        except Exception as e:
            logger.warning("Failed to load metric %s: %s", ep.name, e)
    return metrics


def discover_providers() -> dict[str, type["Provider"]]:
    """Discover all registered providers from installed plugins.

    Returns:
        Dict mapping provider names to their classes
    """
    providers: dict[str, type["Provider"]] = {}
    eps = entry_points(group="checkup.providers")
    for ep in eps:
        try:
            providers[ep.name] = ep.load()
            logger.debug("Discovered provider: %s", ep.name)
        except Exception as e:
            logger.warning("Failed to load provider %s: %s", ep.name, e)
    return providers


def discover_init_templates() -> dict[str, callable]:
    """Discover init templates from installed plugins.

    Returns:
        Dict mapping plugin names to template functions
    """
    templates: dict[str, callable] = {}
    eps = entry_points(group="checkup.init_templates")
    for ep in eps:
        try:
            templates[ep.name] = ep.load()
            logger.debug("Discovered init template: %s", ep.name)
        except Exception as e:
            logger.warning("Failed to load init template %s: %s", ep.name, e)
    return templates


def discover_plugins() -> list[dict[str, str]]:
    """List all installed checkup plugins.

    Returns:
        List of dicts with plugin info (name, version)
    """
    plugins = []
    for dist in distributions():
        name = dist.metadata["Name"]
        if name and name.startswith("checkup-"):
            plugins.append({
                "name": name,
                "version": dist.metadata.get("Version", "unknown"),
            })
    return plugins
