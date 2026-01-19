"""List command implementation."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from checkup.cli.loader import LoadError, load_checkup
from checkup.graph import build_dependency_graph, topological_sort

console = Console()


def list_checkup(
    checkup_file: Annotated[
        Path,
        typer.Argument(help="Python checkup file to inspect"),
    ],
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed information"),
    ] = False,
    metrics_only: Annotated[
        bool,
        typer.Option("--metrics", help="List only metrics"),
    ] = False,
    providers_only: Annotated[
        bool,
        typer.Option("--providers", help="List only providers"),
    ] = False,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: table, json"),
    ] = "table",
) -> None:
    """Inspect a checkup's metrics and providers."""
    # Load the checkup
    try:
        hub = load_checkup(checkup_file)
    except LoadError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"[bold]Checkup:[/bold] {checkup_file}\n")

    # Get execution order (includes dependencies)
    if hub._metrics:
        graph = build_dependency_graph(hub._metrics)
        execution_order = list(topological_sort(graph))
    else:
        execution_order = []

    # Show metrics
    if not providers_only:
        _show_metrics(hub._metrics, execution_order, verbose)

    # Show providers
    if not metrics_only:
        _show_providers(hub._provider_sets, verbose)

    # Show dependency graph
    if verbose and not metrics_only and not providers_only and hub._metrics:
        _show_dependency_graph(hub._metrics)


def _show_metrics(
    metrics: list,
    execution_order: list,
    verbose: bool,
) -> None:
    """Display metrics information."""
    console.print(f"[bold]Metrics ({len(metrics)}):[/bold]")

    if not metrics:
        console.print("  [dim]No metrics registered[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Unit")

    if verbose:
        table.add_column("Dependencies")

    for metric_cls in metrics:
        name = getattr(metric_cls, "name", metric_cls.__name__)
        description = metric_cls.__doc__.split("\n")[0] if metric_cls.__doc__ else ""
        unit = getattr(metric_cls, "unit", "")

        if verbose:
            deps = metric_cls.depends_on() if hasattr(metric_cls, "depends_on") else []
            deps_str = ", ".join(d.name for d in deps) if deps else "-"
            table.add_row(name, description[:50], unit, deps_str)
        else:
            table.add_row(name, description[:50], unit)

    console.print(table)
    console.print()


def _show_providers(
    provider_sets: list,
    verbose: bool,
) -> None:
    """Display provider sets information."""
    console.print(f"[bold]Provider Sets ({len(provider_sets)}):[/bold]")

    if not provider_sets:
        console.print("  [dim]No provider sets configured[/dim]")
        return

    for i, provider_set in enumerate(provider_sets, 1):
        console.print(f"  [bold]Set {i}:[/bold]")
        for provider in provider_set:
            provider_name = type(provider).__name__
            if verbose:
                # Try to show provider attributes
                attrs = []
                for attr, value in vars(provider).items():
                    if not attr.startswith("_"):
                        # Truncate long values
                        str_val = str(value)
                        if len(str_val) > 30:
                            str_val = str_val[:27] + "..."
                        attrs.append(f"{attr}={str_val}")
                if attrs:
                    console.print(f"    - {provider_name} ({', '.join(attrs)})")
                else:
                    console.print(f"    - {provider_name}")
            else:
                console.print(f"    - {provider_name}")

    console.print()


def _show_dependency_graph(metrics: list) -> None:
    """Display the metric dependency graph."""
    console.print("[bold]Dependency Graph:[/bold]")

    # Find root metrics (those without dependents in our set)
    metric_names = {m.name for m in metrics}

    tree = Tree("[bold]Metrics[/bold]")

    def add_metric_to_tree(metric_cls, parent):
        node = parent.add(f"[cyan]{metric_cls.name}[/cyan]")
        deps = metric_cls.depends_on() if hasattr(metric_cls, "depends_on") else []
        for dep in deps:
            add_metric_to_tree(dep, node)

    for metric_cls in metrics:
        add_metric_to_tree(metric_cls, tree)

    console.print(tree)
    console.print()
