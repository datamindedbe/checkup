"""Run command implementation."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from checkup.cli.loader import LoadError, load_checkup
from checkup.materializers import ConsoleMaterializer, CSVMaterializer, HTMLMaterializer

console = Console()


def _get_materializer(
    format: str,
    output: Path | None,
    include_indirect: bool,
):
    """Get the appropriate materializer based on format and output."""
    # Infer format from output extension if not explicitly set
    if output and format == "console":
        suffix = output.suffix.lower()
        if suffix == ".csv":
            format = "csv"
        elif suffix == ".html":
            format = "html"
        elif suffix == ".json":
            format = "json"

    if format == "csv":
        return CSVMaterializer(
            output_path=output,
            include_indirect=include_indirect,
        )
    elif format == "html":
        return HTMLMaterializer(
            output_path=output,
            include_indirect=include_indirect,
        )
    elif format == "json":
        # JSON materializer not yet implemented, fall back to console
        console.print("[yellow]JSON format not yet implemented, using console[/yellow]")
        return ConsoleMaterializer(include_indirect=include_indirect)
    else:
        return ConsoleMaterializer(include_indirect=include_indirect)


def run(
    checkup_file: Annotated[
        Path,
        typer.Argument(help="Python checkup file to execute"),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output file (format inferred from extension)"),
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: console, csv, html, json"),
    ] = "console",
    workers: Annotated[
        Optional[int],
        typer.Option("--workers", "-w", help="Max parallel workers"),
    ] = None,
    include_indirect: Annotated[
        bool,
        typer.Option("--include-indirect", help="Include dependency metrics in output"),
    ] = False,
    verbose: Annotated[
        int,
        typer.Option("--verbose", "-v", count=True, help="Increase verbosity"),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress non-error output"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Validate and show plan without executing"),
    ] = False,
    fail_on_error: Annotated[
        bool,
        typer.Option("--fail-on-error", help="Exit with error code if any metric fails"),
    ] = False,
) -> None:
    """Execute metrics measurement from a checkup file."""
    # Configure logging based on verbosity
    if verbose > 0:
        import logging

        level = logging.WARNING - (verbose * 10)
        logging.basicConfig(level=max(level, logging.DEBUG))

    # Load the checkup
    try:
        hub = load_checkup(checkup_file)
    except LoadError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if dry_run:
        console.print(f"[green]Checkup valid:[/green] {checkup_file}")
        console.print(f"  Metrics: {len(hub._metrics)}")
        console.print(f"  Provider sets: {len(hub._provider_sets)}")
        return

    # Execute measurement
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet,
    ) as progress:
        progress.add_task("Measuring metrics...", total=None)

        try:
            result = hub.measure(max_workers=workers)
        except Exception as e:
            console.print(f"[red]Error during measurement:[/red] {e}")
            raise typer.Exit(1)

    # Output results
    materializer = _get_materializer(format, output, include_indirect)
    result.materialize(materializer)

    if output:
        console.print(f"[green]Results written to:[/green] {output}")

    # Report errors
    if result.errors:
        console.print(f"\n[yellow]Warnings:[/yellow] {len(result.errors)} provider set(s) failed")
        for providers, error in result.errors:
            provider_names = [type(p).__name__ for p in providers]
            console.print(f"  - {provider_names}: {error}")

        if fail_on_error:
            raise typer.Exit(2)
