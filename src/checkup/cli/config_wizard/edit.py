"""
Interactive config editing.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from checkup.configuration import load_config
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


def edit_config(config_path: Path | None = None) -> None:
    """
    Interactively edit an existing config file.
    """

    path = config_path or Path.cwd() / CONFIG_FILENAME

    if not path.exists():
        console.print(f"[red]Config file not found: {path}[/red]", markup=True)
        console.print("Run [bold]checkup init[/bold] to create one.", markup=True)
        return

    config = load_config(config_path=path)
    registry = get_registry()

    console.print(f"[bold]Editing {path}[/bold]\n", markup=True)
    _show_current_config(config)

    config_new = _build_config(config, registry)

    if config_new is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return

    write_config(path, config_new)


def _build_config(
    config: CheckupConfig, registry: "PluginRegistry"
) -> CheckupConfig | None:
    provider_configs = {p.name: p.config for p in config.providers}
    metric_configs = {m.type: m.config for m in config.metrics}

    tags = _prompt_edit_tags(config)
    if tags is None:
        return None

    provider_names = _prompt_edit_providers(config, registry)
    if provider_names is None:
        return None

    metric_names = _prompt_edit_metrics(config, registry, provider_names)
    if metric_names is None:
        return None

    mat = _prompt_edit_materializer(config, registry)
    if mat is None:
        return None

    return CheckupConfig(
        tags=tags,
        providers=[
            ProviderConfig(name=p, config=provider_configs.get(p, {}))
            for p in provider_names
        ],
        metrics=[
            MetricConfig(type=m, config=metric_configs.get(m, {})) for m in metric_names
        ],
        materializer=MaterializerConfig(type=mat) if mat else None,
    )


def _prompt_edit_tags(config: "CheckupConfig") -> dict | None:
    edit = get_questionary().confirm("Edit tags?", default=False).ask()
    if edit is None:
        return None
    elif edit:
        return _edit_tags(dict(config.tags))
    return dict(config.tags)


def _prompt_edit_providers(
    config: "CheckupConfig",
    registry: "PluginRegistry",
) -> list[str] | None:
    current_names = [p.name for p in config.providers]

    edit = get_questionary().confirm("Edit providers?", default=False).ask()
    if edit is None:
        return None
    elif edit:
        return select_multiple(
            registry.list_provider_names(),
            current_names,
            "providers",
        )
    return current_names


def _prompt_edit_metrics(
    config: "CheckupConfig",
    registry: "PluginRegistry",
    provider_names: list[str],
) -> list[str] | None:
    current_types = [m.type for m in config.metrics]

    with console.status("Loading metrics..."):
        available = registry.list_compatible_metric_names(provider_names)

    edit = get_questionary().confirm("Edit metrics?", default=False).ask()
    if edit is None:
        return None
    elif edit:
        return select_multiple(available, current_types, "metrics")
    return [m.type for m in config.metrics if m.type in available]


def _prompt_edit_materializer(
    config: "CheckupConfig",
    registry: "PluginRegistry",
) -> str | None:
    edit = get_questionary().confirm("Edit materializer?", default=False).ask()
    if edit is None:
        return None
    elif edit:
        return select_materializer(
            config.materializer.type if config.materializer else None,
            registry,
        )
    return config.materializer.type if config.materializer else ""


def _edit_tags(tags: dict) -> dict | None:
    console.print(f"Current tags: {tags or '(none)'}")

    while True:
        action: str | None = (
            get_questionary()
            .select(
                "Action:",
                choices=["done", "add", "remove"],
            )
            .ask()
        )

        if action is None:
            return None
        if action == "done":
            break
        elif action == "add":
            tag: str | None = get_questionary().text("Tag (key=value):").ask()
            if tag is None:
                return None
            if tag and "=" in tag:
                key, value = tag.split("=", 1)
                tags[key.strip()] = value.strip()
        elif action == "remove" and tags:
            key = (
                get_questionary()
                .select(
                    "Key to remove:",
                    choices=list(tags.keys()),
                )
                .ask()
            )
            if key is None:
                return None
            if key:
                tags.pop(key, None)

    return tags


def _show_current_config(config: "CheckupConfig") -> None:
    console.print("[bold]Current configuration:[/bold]", markup=True)
    console.print(f"  Tags: {dict(config.tags) or '(none)'}")
    console.print(f"  Providers: {[p.name for p in config.providers] or '(none)'}")
    console.print(f"  Metrics: {[m.type for m in config.metrics] or '(none)'}")
    mat = config.materializer.type if config.materializer else "(none)"
    console.print(f"  Materializer: {mat}")
    console.print()
