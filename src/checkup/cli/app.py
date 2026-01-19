"""Checkup CLI application."""

import typer

from checkup.cli.commands import init, list_cmd, run, validate, version

app = typer.Typer(
    name="checkup",
    help="Extensible metrics calculation framework",
    no_args_is_help=True,
)

# Register commands
app.command(name="run")(run.run)
app.command(name="list")(list_cmd.list_checkup)
app.command(name="validate")(validate.validate)
app.command(name="init")(init.init)
app.command(name="version")(version.version)


def main() -> None:
    """CLI entry point."""
    app()
