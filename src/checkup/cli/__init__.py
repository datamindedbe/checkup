"""
Checkup CLI application.
"""

import typer

from checkup.cli.commands import config, init, run, schema

app = typer.Typer(
    name="checkup",
    help="CheckUp - Computational governance framework for measuring data product health",
    no_args_is_help=True,
)

app.command()(run)
app.command()(init)
app.command()(config)
app.command()(schema)
