"""
Execute checkhub from CLI configuration.
"""

import logging
from typing import TYPE_CHECKING

from rich.console import Console

from checkup.configuration import CheckupConfig
from checkup.hub import CheckHub
from checkup.materializers import ConsoleMaterializer
from checkup.providers.tags import TagProvider
from checkup.registry import get_registry

if TYPE_CHECKING:
    from checkup.materializers import Materializer
    from checkup.metric import Metric
    from checkup.provider import Provider
    from checkup.registry.discovery import PluginRegistry

logger = logging.getLogger(__name__)
console = Console()


def execute_checkup(config: CheckupConfig, materializer: str | None = None) -> None:
    """
    Execute checkup with the given configuration.

    Args:
        config: Loaded checkup configuration
        materializer: Override materializer type (e.g., "console")
    """

    registry = get_registry()

    providers = _resolve_providers(config, registry)
    if not providers:
        console.print("[yellow]No providers configured[/yellow]")
        return

    metrics = _resolve_metrics(config, registry)
    if not metrics:
        console.print("[yellow]No metrics configured[/yellow]")
        return

    materializer = _resolve_materializer(config, registry, materializer)

    console.print(f"[blue]Running {len(metrics)} metrics...[/blue]")

    result = CheckHub().with_metrics(metrics).with_providers([providers]).measure()

    if result.errors:
        for _, error in result.errors:
            console.print(f"[red]Error: {error}[/red]")

    result.materialize(materializer)


def _resolve_providers(
    config: CheckupConfig,
    registry: "PluginRegistry",
) -> list["Provider"]:
    """
    Resolve provider configs to provider instances.
    """

    providers: list[Provider] = []

    if config.tags:
        providers.append(TagProvider(**config.tags))

    for provider_config in config.providers:
        provider_cls = registry.get_provider(provider_config.name)
        if provider_cls is None:
            console.print(f"[yellow]Unknown provider: {provider_config.name}[/yellow]")
            continue

        try:
            provider = provider_cls(**provider_config.config)
            providers.append(provider)
        except Exception as e:
            console.print(
                f"[red]Failed to instantiate provider {provider_config.name}: {e}[/red]"
            )

    return providers


def _resolve_metrics(
    config: CheckupConfig,
    registry: "PluginRegistry",
) -> list["Metric"]:
    """
    Resolve metric configs to metric instances.
    """

    metrics: list[Metric] = []

    for metric_config in config.metrics:
        metric_cls = registry.get_metric(metric_config.name)
        if metric_cls is None:
            console.print(f"[yellow]Unknown metric: {metric_config.name}[/yellow]")
            continue

        try:
            metric = metric_cls(**metric_config.config)
            metrics.append(metric)
        except Exception as e:
            console.print(
                f"[red]Failed to instantiate metric {metric_config.name}: {e}[/red]"
            )

    return metrics


def _resolve_materializer(
    config: CheckupConfig,
    registry: "PluginRegistry",
    override: str | None = None,
) -> "Materializer":
    """
    Resolve materializer config to materializer instance.
    """

    if override:
        mat_type = override
        mat_config = {}
    elif config.materializer:
        mat_type = config.materializer.type
        mat_config = config.materializer.config
    else:
        mat_type = "console"
        mat_config = {}

    materializer_cls = registry.get_materializer(mat_type)

    if materializer_cls is None:
        console.print(
            f"[yellow]Unknown materializer: {mat_type}, using console[/yellow]"
        )
        return ConsoleMaterializer()

    try:
        return materializer_cls(**mat_config)
    except Exception as e:
        console.print(f"[red]Failed to instantiate materializer {mat_type}: {e}[/red]")
        return ConsoleMaterializer()
