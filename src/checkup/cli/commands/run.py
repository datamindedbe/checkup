"""
Run command. Run metrics and materialize results.
"""

import logging
from pathlib import Path
from typing import Annotated

import typer

from checkup.cli.executor import execute_checkup
from checkup.cli.utils import apply_cli_overrides
from checkup.configuration import load_config


def run(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to config file"),
    ] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option("--tag", "-t", help="Set tags (key=value)"),
    ] = None,
    provider: Annotated[
        list[str] | None,
        typer.Option("--provider", "-p", help="Set providers (name or name:key=value)"),
    ] = None,
    metric: Annotated[
        list[str] | None,
        typer.Option("--metric", "-m", help="Set metrics (name or name:key=value)"),
    ] = None,
    materializer: Annotated[
        str | None,
        typer.Option(
            "--materializer", help="Set materializer (type or type:key=value)"
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Don't materialize, just print"),
    ] = False,
    multiprocessing: Annotated[
        bool,
        typer.Option(
            "--multiprocessing",
            help="When disabled, run sequentially without subprocesses",
        ),
    ] = True,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Verbose output"),
    ] = False,
) -> None:
    """
    Run metrics and materialize results.
    """

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    cfg = load_config(config_path=config)
    cfg = apply_cli_overrides(cfg, tag, provider, metric)

    execute_checkup(
        cfg,
        materializer="console" if dry_run else materializer,
        multiprocessing=multiprocessing,
    )
