"""
Shared utilities for the config wizard.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from rich.console import Console

from checkup.configuration.io import SCHEMA_FILENAME
from checkup.configuration.models import CheckupConfig
from checkup.configuration.schema import write_schema

if TYPE_CHECKING:
    import questionary

    from checkup.registry import PluginRegistry

console = Console(markup=False, highlight=False)


def get_questionary() -> "questionary":
    """
    Lazy import questionary to avoid slow startup.
    """

    import questionary

    return questionary


def select_multiple(
    available: list[str],
    selected: list[str],
    item_name: str,
) -> list[str]:
    """
    Select multiple items with fuzzy search.
    """

    if not available:
        console.print(
            f"[yellow]No {item_name} found. Install checkup plugins.[/yellow]",
            markup=True,
        )
        return []

    selected_count = len([s for s in selected if s in available])
    console.print(f"Currently selected: {selected_count}/{len(available)} {item_name}")

    choices = [
        get_questionary().Choice(name, checked=name in selected)
        for name in sorted(available)
    ]

    result = (
        get_questionary()
        .checkbox(
            f"Select {item_name}:",
            choices=choices,
            use_search_filter=True,
            use_jk_keys=False,
            instruction="(↑↓ navigate, space toggle, type to filter, enter confirm)",
        )
        .ask()
    )

    return result or []


def select_materializer(current: str | None, registry: "PluginRegistry") -> str | None:
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
        get_questionary()
        .select(
            "Materializer type:",
            choices=available,
            default=default,
            use_search_filter=True,
            use_jk_keys=False,
        )
        .ask()
    )


def write_config(path: Path, config: CheckupConfig) -> None:
    """
    Write config to file with empty lines between sections.
    Also generates the JSON schema file.
    """

    console.print(f"\n[bold]Writing config to {path}[/bold]", markup=True)

    data = config.model_dump(exclude_defaults=True)

    lines = [f"# yaml-language-server: $schema={SCHEMA_FILENAME}"]

    # Write sections separately with blank lines between them
    for key in CheckupConfig.model_fields:
        if key not in data or not data[key]:
            continue
        lines.append("")
        lines.append(
            yaml.dump(
                {key: data[key]}, default_flow_style=False, sort_keys=False
            ).rstrip()
        )

    with open(path, "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    schema_path = path.parent / SCHEMA_FILENAME
    write_schema(schema_path)
    console.print(f"[green]Schema written to {schema_path}[/green]", markup=True)

    console.print("[green]Done![/green]", markup=True)
    console.print(
        "Run [bold]checkup run[/bold] to test your configuration.", markup=True
    )
