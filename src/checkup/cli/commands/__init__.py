"""
CLI commands.
"""

from checkup.cli.commands.config import config
from checkup.cli.commands.init import init
from checkup.cli.commands.plugins import plugins
from checkup.cli.commands.run import run
from checkup.cli.commands.schema import schema

__all__ = [
    "config",
    "init",
    "plugins",
    "run",
    "schema",
]
