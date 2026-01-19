"""Validate command implementation."""

import pickle
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from checkup.cli.loader import LoadError, load_checkup
from checkup.graph import build_dependency_graph, topological_sort
from checkup.validators import validate_providers, validate_unique_metric_names

console = Console()


def validate(
    checkup_file: Annotated[
        Path,
        typer.Argument(help="Python checkup file to validate"),
    ],
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed validation output"),
    ] = False,
) -> None:
    """Validate a checkup without executing."""
    console.print(f"Validating {checkup_file}...\n")

    errors = []

    # 1. Check Python syntax and load module
    try:
        hub = load_checkup(checkup_file)
        _print_check("Python syntax valid", True, verbose)
        _print_check("CheckUp found", True, verbose)
    except LoadError as e:
        _print_check("Python syntax valid", False, verbose)
        console.print(f"  [red]{e}[/red]")
        raise typer.Exit(1)

    # 2. Check metrics registered
    metric_count = len(hub._metrics)
    if metric_count > 0:
        _print_check(f"{metric_count} metrics registered", True, verbose)
    else:
        _print_check("No metrics registered", False, verbose)
        errors.append("No metrics registered")

    # 3. Check provider sets configured
    provider_count = len(hub._provider_sets)
    _print_check(f"{provider_count} provider sets configured", True, verbose)

    # 4. Validate dependency graph (no cycles)
    try:
        if hub._metrics:
            graph = build_dependency_graph(hub._metrics)
            execution_order = list(topological_sort(graph))
            _print_check("Dependency graph valid (no cycles)", True, verbose)
        else:
            execution_order = []
            _print_check("Dependency graph valid (no cycles)", True, verbose)
    except Exception as e:
        _print_check("Dependency graph valid", False, verbose)
        console.print(f"  [red]{e}[/red]")
        errors.append(str(e))

    # 5. Validate unique metric names
    try:
        if execution_order:
            validate_unique_metric_names(execution_order)
        _print_check("No duplicate metric names", True, verbose)
    except Exception as e:
        _print_check("No duplicate metric names", False, verbose)
        console.print(f"  [red]{e}[/red]")
        errors.append(str(e))

    # 6. Validate provider requirements
    try:
        provider_sets = hub._provider_sets if hub._provider_sets else [[]]
        if execution_order:
            validate_providers(execution_order, provider_sets)
        _print_check("Provider requirements satisfied", True, verbose)
    except Exception as e:
        _print_check("Provider requirements satisfied", False, verbose)
        console.print(f"  [red]{e}[/red]")
        errors.append(str(e))

    # 7. Check metrics are pickleable
    try:
        for metric_cls in hub._metrics:
            instance = metric_cls()
            pickle.dumps(instance)
        _print_check("All metrics pickleable", True, verbose)
    except Exception as e:
        _print_check("All metrics pickleable", False, verbose)
        console.print(f"  [red]{e}[/red]")
        errors.append(f"Metric not pickleable: {e}")

    # Summary
    console.print()
    if errors:
        console.print(f"[red]Validation failed with {len(errors)} error(s).[/red]")
        raise typer.Exit(1)
    else:
        console.print("[green]Valid.[/green]")


def _print_check(message: str, success: bool, verbose: bool) -> None:
    """Print a validation check result."""
    if success:
        console.print(f"[green]\u2713[/green] {message}")
    else:
        console.print(f"[red]\u2717[/red] {message}")
