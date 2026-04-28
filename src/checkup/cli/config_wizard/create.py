"""
Interactive config creation.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from checkup.configuration.io import CONFIG_FILENAME
from checkup.configuration.models import (
    CheckupConfig,
    MaterializerConfig,
    MetricConfig,
    ProviderConfig,
)
from checkup.registry import get_registry

from ._common import (
    console,
    get_questionary,
    select_materializer,
    select_multiple,
    write_config,
)

if TYPE_CHECKING:
    from checkup.registry import PluginRegistry


def create_config(output_path: Path | None = None) -> None:
    """
    Interactively create a new config file.
    """

    path = output_path or Path.cwd() / CONFIG_FILENAME

    if not _confirm_overwrite(path):
        return

    registry = get_registry()
    config = _build_config(registry)

    if config is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return

    write_config(path, config)


def _confirm_overwrite(path: Path) -> bool:
    if not path.exists():
        return True

    overwrite = (
        get_questionary().confirm(f"{path} exists. Overwrite?", default=False).ask()
    )
    if overwrite is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return False
    return overwrite


def _build_config(registry: "PluginRegistry") -> CheckupConfig | None:
    tags = _prompt_tags()
    if tags is None:
        return None

    provider_names = _prompt_providers(registry)
    if provider_names is None:
        return None

    metric_names = _prompt_metrics(registry, provider_names)
    if metric_names is None:
        return None

    mat = _prompt_materializer(registry)
    if mat is None:
        return None

    return CheckupConfig(
        tags=tags,
        providers=[ProviderConfig(name=p) for p in provider_names],
        metrics=[MetricConfig(type=m) for m in metric_names],
        materializer=MaterializerConfig(type=mat) if mat != "console" else None,
    )


def _prompt_tags() -> dict[str, str] | None:
    console.print("\n[bold]Tags[/bold]", markup=True)
    console.print(
        "Tags identify your data product (e.g., product=my-product, team=analytics)"
    )
    return _collect_tags()


def _prompt_providers(registry: "PluginRegistry") -> list[str] | None:
    console.print("\n[bold]Providers[/bold]", markup=True)
    return select_multiple(registry.list_provider_names(), [], "providers")


def _prompt_metrics(
    registry: "PluginRegistry", provider_names: list[str]
) -> list[str] | None:
    console.print("\n[bold]Metrics[/bold]", markup=True)
    with console.status("Loading metrics..."):
        available_metrics = registry.list_compatible_metric_names(provider_names)
    return select_multiple(available_metrics, [], "metrics")


def _prompt_materializer(registry: "PluginRegistry") -> str | None:
    console.print("\n[bold]Materializer[/bold]", markup=True)
    return select_materializer(None, registry)


def _collect_tags() -> dict[str, str] | None:
    tags: dict[str, str] = {}

    while True:
        tag: str = (
            get_questionary()
            .text(
                "Add tag (key=value, or empty to finish):",
            )
            .ask()
        )

        if tag is None:
            return None
        if not tag:
            break
        if "=" in tag:
            key, value = tag.split("=", 1)
            tags[key.strip()] = value.strip()

    return tags
