"""Init command implementation."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from checkup.discovery import discover_init_templates

console = Console()

# Default template when no plugin is specified
DEFAULT_TEMPLATE = '''"""Project health metrics."""

from checkup import CheckUp
from checkup.providers.tags import TagProvider

hub = (
    CheckUp()
    # Add your metrics here
    # .with_metrics([...])
    # Add your provider sets here
    # Each provider set represents one context (project, environment, etc.)
    # .with_providers([
    #     [SomeProvider(...), TagProvider(project="my-project")],
    # ])
)
'''


def init(
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
    plugin: Annotated[
        Optional[str],
        typer.Option("--plugin", "-p", help="Plugin to generate template for"),
    ] = None,
    list_plugins: Annotated[
        bool,
        typer.Option("--list", "-l", help="List available plugins"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing file"),
    ] = False,
) -> None:
    """Generate a starter checkup file."""
    templates = discover_init_templates()

    # List available plugins
    if list_plugins:
        console.print("[bold]Available plugins:[/bold]")
        if templates:
            for name in sorted(templates.keys()):
                console.print(f"  {name}")
        else:
            console.print("  [dim]No plugins with templates installed[/dim]")
        return

    # Determine output path
    if output is None:
        output = Path("checkup.py")

    # Check if file exists
    if output.exists() and not force:
        console.print(f"[red]Error:[/red] {output} already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    # Get template content
    if plugin:
        if plugin not in templates:
            console.print(f"[red]Error:[/red] Unknown plugin '{plugin}'")
            console.print("Available plugins:")
            for name in sorted(templates.keys()):
                console.print(f"  {name}")
            raise typer.Exit(1)

        try:
            template_fn = templates[plugin]
            content = template_fn()
        except Exception as e:
            console.print(f"[red]Error getting template:[/red] {e}")
            raise typer.Exit(1)
    else:
        content = DEFAULT_TEMPLATE

    # Write the file
    output.write_text(content)
    console.print(f"[green]Created:[/green] {output}")

    if plugin:
        console.print(f"\nGenerated template for [bold]{plugin}[/bold] plugin.")
    else:
        console.print("\nGenerated basic template. Use --plugin <name> for plugin-specific templates.")

    console.print(f"\nNext steps:")
    console.print(f"  1. Edit {output} to configure your metrics and providers")
    console.print(f"  2. Run: checkup validate {output}")
    console.print(f"  3. Run: checkup run {output}")
