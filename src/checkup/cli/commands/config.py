"""
Config command. Modify an existing config file.
"""

from pathlib import Path
from typing import Annotated

import typer

from checkup.cli.config_wizard import edit_config


def config(
    config_path: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to config file"),
    ] = None,
) -> None:
    """
    Modify the checkup.yaml config file.
    """

    edit_config(config_path=config_path)
