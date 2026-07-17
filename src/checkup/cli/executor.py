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
from checkup.selection import select_metrics

if TYPE_CHECKING:
    from checkup.materializers import Materializer
    from checkup.metric import Metric
    from checkup.provider import Provider
    from checkup.registry.discovery import PluginRegistry

logger = logging.getLogger(__name__)
console = Console()


def execute_checkup(
    config: CheckupConfig,
    materializer: str | None = None,
    multiprocessing: bool = True,
    quiet: bool = False,
    select: str | None = None,
    exclude: str | None = None,
) -> None:
    """
    Execute checkup with the given configuration.

    Args:
        config: Loaded checkup configuration
        materializer: Override materializer type (e.g., "console")
        multiprocessing: If False, run sequentially without subprocesses
        quiet: If True, send status/errors to stderr so stdout holds only the materializer output.
        select: Selector for which metrics to materialize.
        exclude: Selector for metrics to exclude from materialization.
    """

    out = Console(stderr=True) if quiet else console

    registry = get_registry()

    providers = _resolve_providers(config, registry, out)
    if not providers:
        out.print("[yellow]No providers configured[/yellow]")
        return

    metrics = _resolve_metrics(config, registry, out)
    if not metrics:
        out.print("[yellow]No metrics configured[/yellow]")
        return

    materializer = _resolve_materializer(config, registry, materializer, out)

    select = select if select is not None else config.select
    exclude = exclude if exclude is not None else config.exclude
    type_by_name = {mc.instance_name: mc.type for mc in config.metrics}

    out.print(f"[blue]Running {len(metrics)} metrics...[/blue]")

    result = (
        CheckHub()
        .with_metrics(metrics)
        .with_providers([providers])
        .measure(multiprocessing=multiprocessing)
    )

    if result.errors:
        for _, error in result.errors:
            out.print(f"[red]Error: {error}[/red]")

    if select or exclude:
        selected = select_metrics(
            metrics,
            select=select,
            exclude=exclude,
            type_resolver=lambda metric: type_by_name.get(metric.name),
        )
        result.measurements = [
            m for m in result.measurements if m.metric.name in selected
        ]
        result.direct_metric_names = result.direct_metric_names & selected

        console.print(
            f"[blue]Materializing {len(selected)} selected of {len(metrics)} total metrics[/blue]"
        )

    result.materialize(materializer)


def _resolve_providers(
    config: CheckupConfig,
    registry: "PluginRegistry",
    out: Console = console,
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
            out.print(f"[yellow]Unknown provider: {provider_config.name}[/yellow]")
            continue

        try:
            provider = provider_cls(**provider_config.config)
            providers.append(provider)
        except Exception as e:
            out.print(
                f"[red]Failed to instantiate provider {provider_config.name}: {e}[/red]"
            )

    return providers


def _resolve_metrics(
    config: CheckupConfig,
    registry: "PluginRegistry",
    out: Console = console,
) -> list["Metric"]:
    """
    Resolve metric configs to metric instances.
    """

    metrics: list[Metric] = []

    for metric_config in config.metrics:
        metric_cls = registry.get_metric(metric_config.type)
        if metric_cls is None:
            out.print(f"[yellow]Unknown metric: {metric_config.type}[/yellow]")
            continue

        try:
            metrics.append(
                metric_cls(
                    **metric_config.config,
                    **({"name": metric_config.name} if metric_config.name else {}),
                )
            )
        except Exception as e:
            out.print(
                f"[red]Failed to instantiate metric {metric_config.type}: {e}[/red]"
            )

    return metrics


def _resolve_materializer(
    config: CheckupConfig,
    registry: "PluginRegistry",
    override: str | None = None,
    out: Console = console,
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
        out.print(f"[yellow]Unknown materializer: {mat_type}, using console[/yellow]")
        return ConsoleMaterializer()

    try:
        return materializer_cls(**mat_config)
    except Exception as e:
        out.print(f"[red]Failed to instantiate materializer {mat_type}: {e}[/red]")
        return ConsoleMaterializer()
