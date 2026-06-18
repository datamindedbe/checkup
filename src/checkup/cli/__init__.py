"""
Checkup CLI application.
"""

from importlib.metadata import version as pkg_version
from typing import Annotated

import typer

from checkup.cli.commands import config, init, plugins, run, schema

app = typer.Typer(
    name="checkup",
    help="CheckUp - Computational governance framework for measuring data product health",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(pkg_version("checkup"))
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", "-v", callback=version_callback),
    ] = None,
) -> None:
    pass


app.command()(run)
app.command()(init)
app.command()(config)
app.command()(schema)
app.command()(plugins)
