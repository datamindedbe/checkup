"""
Init command. Create a new config file.
"""

from pathlib import Path
from typing import Annotated

import typer

from checkup.cli.config_wizard import create_config


def init(
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output path for config file"),
    ] = None,
) -> None:
    """
    Create a checkup.yaml config file.
    """

    create_config(output_path=output)
