"""
Interactive config generation and editing.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from rich.console import Console

from checkup.configuration.io import CONFIG_FILENAME
from checkup.configuration.schema import write_schema
from checkup.registry import get_registry

if TYPE_CHECKING:
    import questionary

    from checkup.configuration import CheckupConfig
    from checkup.registry import PluginRegistry

console = Console(markup=False, highlight=False)


def _get_questionary() -> "questionary":
    """
    Lazy import questionary to avoid slow startup.
    """

    import questionary

    return questionary


def create_config(output_path: Path | None = None) -> None:
    """
    Interactively create a new config file.
    """

    path = output_path or Path.cwd() / CONFIG_FILENAME

    if path.exists():
        overwrite = (
            _get_questionary()
            .confirm(f"{path} exists. Overwrite?", default=False)
            .ask()
        )
        if overwrite is None or not overwrite:
            if overwrite is None:
                console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
            return

    registry = get_registry()
    config: dict = {}

    # Tags
    console.print("\n[bold]Tags[/bold]", markup=True)
    console.print(
        "Tags identify your data product (e.g., product=my-product, team=analytics)"
    )
    tags = _collect_tags({})
    if tags is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return
    if tags:
        config["tags"] = tags

    # Providers
    console.print("\n[bold]Providers[/bold]", markup=True)
    provider_names = _select_multiple(registry.list_provider_names(), [], "providers")
    if provider_names is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return
    if provider_names:
        config["providers"] = [{"name": p} for p in provider_names]

    # Metrics
    console.print("\n[bold]Metrics[/bold]", markup=True)
    with console.status("Loading metrics..."):
        available_metrics = registry.list_compatible_metric_names(provider_names or [])
    metric_names = _select_multiple(available_metrics, [], "metrics")
    if metric_names is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return
    if metric_names:
        config["metrics"] = [{"name": m} for m in metric_names]

    # Materializer
    console.print("\n[bold]Materializer[/bold]", markup=True)
    mat = _select_materializer(None, registry)
    if mat is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return
    if mat != "console":
        config["materializer"] = {"type": mat}

    # Write
    _write_config(path, config)


def edit_config(config_path: Path | None = None) -> None:
    """
    Interactively edit an existing config file.
    """

    from checkup.configuration import load_config

    path = config_path or Path.cwd() / CONFIG_FILENAME

    if not path.exists():
        console.print(f"[red]Config file not found: {path}[/red]", markup=True)
        console.print("Run [bold]checkup init[/bold] to create one.", markup=True)
        return

    cfg = load_config(config_path=path)
    registry = get_registry()

    console.print(f"[bold]Editing {path}[/bold]\n", markup=True)
    _show_current_config(cfg)

    new_config: dict = {}

    # Build lookup for existing configs
    existing_provider_configs = {p.name: p.config for p in cfg.providers}
    existing_metric_configs = {m.name: m.config for m in cfg.metrics}

    # Tags
    edit_tags = _get_questionary().confirm("Edit tags?", default=False).ask()
    if edit_tags is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return
    if edit_tags:
        tags = _edit_tags(dict(cfg.tags))
        if tags is None:
            console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
            return
        if tags:
            new_config["tags"] = tags
    elif cfg.tags:
        new_config["tags"] = dict(cfg.tags)

    # Providers
    current_provider_names = [p.name for p in cfg.providers]
    edit_providers = _get_questionary().confirm("Edit providers?", default=False).ask()
    if edit_providers is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return
    if edit_providers:
        provider_names = _select_multiple(
            registry.list_provider_names(),
            current_provider_names,
            "providers",
        )
        if provider_names is None:
            console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
            return
        if provider_names:
            # Preserve existing config for re-selected providers
            new_config["providers"] = [
                {"name": p, **existing_provider_configs.get(p, {})}
                for p in provider_names
            ]
    else:
        provider_names = current_provider_names
        if provider_names:
            new_config["providers"] = [
                {"name": p.name, **p.config} for p in cfg.providers
            ]

    # Metrics
    current_metric_names = [m.name for m in cfg.metrics]
    with console.status("Loading metrics..."):
        available_metrics = registry.list_compatible_metric_names(provider_names)
    edit_metrics = _get_questionary().confirm("Edit metrics?", default=False).ask()
    if edit_metrics is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return
    if edit_metrics:
        metric_names = _select_multiple(
            available_metrics,
            current_metric_names,
            "metrics",
        )
        if metric_names is None:
            console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
            return
        if metric_names:
            # Preserve existing config for re-selected metrics
            new_config["metrics"] = [
                {"name": m, **existing_metric_configs.get(m, {})} for m in metric_names
            ]
    elif current_metric_names:
        new_config["metrics"] = [
            {"name": m.name, **m.config}
            for m in cfg.metrics
            if m.name in available_metrics
        ]

    # Materializer
    edit_mat = _get_questionary().confirm("Edit materializer?", default=False).ask()
    if edit_mat is None:
        console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
        return
    if edit_mat:
        mat = _select_materializer(
            cfg.materializer.type if cfg.materializer else None,
            registry,
        )
        if mat is None:
            console.print("\n[yellow]Cancelled.[/yellow]", markup=True)
            return
        new_config["materializer"] = {"type": mat}
    elif cfg.materializer:
        new_config["materializer"] = {"type": cfg.materializer.type}

    _write_config(path, new_config)


def _show_current_config(cfg: "CheckupConfig") -> None:
    """
    Display current configuration.
    """

    console.print("[bold]Current configuration:[/bold]", markup=True)
    console.print(f"  Tags: {dict(cfg.tags) or '(none)'}")
    console.print(f"  Providers: {[p.name for p in cfg.providers] or '(none)'}")
    console.print(f"  Metrics: {[m.name for m in cfg.metrics] or '(none)'}")
    mat = cfg.materializer.type if cfg.materializer else "(none)"
    console.print(f"  Materializer: {mat}")
    console.print()


def _collect_tags(existing: dict) -> dict | None:
    """
    Collect tags interactively. Returns None if cancelled.
    """

    tags = dict(existing)

    while True:
        tag = (
            _get_questionary()
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


def _edit_tags(tags: dict) -> dict | None:
    """
    Edit tags interactively. Returns None if cancelled.
    """

    console.print(f"Current tags: {tags or '(none)'}")

    while True:
        action = (
            _get_questionary()
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
            tag = _get_questionary().text("Tag (key=value):").ask()
            if tag is None:
                return None
            if tag and "=" in tag:
                key, value = tag.split("=", 1)
                tags[key.strip()] = value.strip()
        elif action == "remove" and tags:
            key = (
                _get_questionary()
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


def _select_multiple(
    available: list[str],
    selected: list[str],
    item_type: str,
) -> list[str]:
    """
    Select multiple items with fuzzy search.
    """

    if not available:
        console.print(
            f"[yellow]No {item_type} found. Install checkup plugins.[/yellow]",
            markup=True,
        )
        return []

    # Show current state
    selected_count = len([s for s in selected if s in available])
    console.print(f"Currently selected: {selected_count}/{len(available)} {item_type}")

    choices = [
        _get_questionary().Choice(name, checked=name in selected)
        for name in sorted(available)
    ]

    result = (
        _get_questionary()
        .checkbox(
            f"Select {item_type}:",
            choices=choices,
            use_search_filter=True,
            use_jk_keys=False,
            instruction="(↑↓ navigate, space toggle, type to filter, enter confirm)",
        )
        .ask()
    )

    return result or []


def _select_materializer(current: str | None, registry: "PluginRegistry") -> str | None:
    """
    Select materializer interactively.
    """

    available = registry.list_materializer_names()

    if not available:
        return "console"

    default = (
        current if current in available else (available[0] if available else "console")
    )

    return (
        _get_questionary()
        .select(
            "Materializer type:",
            choices=available,
            default=default,
            use_search_filter=True,
            use_jk_keys=False,
        )
        .ask()
    )


def _write_config(path: Path, config: dict) -> None:
    """
    Write config to file with empty lines between sections.
    Also generates the JSON schema file.
    """

    console.print(f"\n[bold]Writing config to {path}[/bold]", markup=True)

    # Write sections separately with blank lines between them
    lines = ["# yaml-language-server: $schema=checkup.schema.json"]

    for key in ["tags", "providers", "metrics", "materializer"]:
        if key in config:
            lines.append("")
            lines.append(
                yaml.dump(
                    {key: config[key]}, default_flow_style=False, sort_keys=False
                ).rstrip()
            )

    with open(path, "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    # Generate schema file
    schema_path = path.parent / "checkup.schema.json"
    write_schema(schema_path)
    console.print(f"[green]Schema written to {schema_path}[/green]", markup=True)

    console.print("[green]Done![/green]", markup=True)
    console.print(
        "Run [bold]checkup run[/bold] to test your configuration.", markup=True
    )
