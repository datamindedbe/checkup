"""
Plugins command. List installed checkup plugins.
"""

from rich.console import Console
from rich.table import Table

from checkup.registry import get_registry

console = Console()


def plugins() -> None:
    """
    List installed checkup plugins.
    """

    all_plugins = get_registry().list_plugins()
    all_plugins.pop("checkup", None)

    if not all_plugins:
        console.print("[yellow]No checkup plugins installed[/yellow]")
        return

    kinds = [
        ("Providers", "providers"),
        ("Metrics", "metrics"),
        ("Materializers", "materializers"),
    ]
    populated_kinds = [
        (header, attr)
        for header, attr in kinds
        if any(getattr(p, attr) for p in all_plugins.values())
    ]

    table = Table(title="Installed checkup plugins")
    table.add_column("Plugin", style="bold", overflow="fold")
    table.add_column("Version", overflow="fold")
    for header, _ in populated_kinds:
        table.add_column(header, overflow="fold")

    for name, plugin in all_plugins.items():
        table.add_row(
            name,
            plugin.version or "",
            *("\n".join(getattr(plugin, attr)) for _, attr in populated_kinds),
        )

    console.print(table)
