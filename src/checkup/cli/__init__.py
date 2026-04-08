"""
Checkup CLI application.
"""

import typer

from checkup.cli.commands import check, config, init, run, schema

app = typer.Typer(
    name="checkup",
    help="CheckUp - Computational governance framework for measuring data product health",
    no_args_is_help=True,
)

app.command()(check)
app.command()(run)
app.command()(init)
app.command()(config)
app.command()(schema)


def main() -> None:
    """
    CLI entry point.
    """

    app()
