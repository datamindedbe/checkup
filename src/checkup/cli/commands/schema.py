"""
Schema command. Generate JSON schema for checkup.yaml.
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from checkup.configuration.io import SCHEMA_FILENAME
from checkup.configuration.schema import write_schema

console = Console()


def schema(
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output path for schema file"),
    ] = None,
) -> None:
    """
    Generate JSON schema for checkup.yaml.
    """

    path = output or Path.cwd() / SCHEMA_FILENAME
    write_schema(path)
    console.print(f"[green]Schema written to {path}[/green]")
