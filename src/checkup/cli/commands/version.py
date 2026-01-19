"""Version command implementation."""

import sys
from importlib.metadata import version as pkg_version

from rich.console import Console

from checkup.discovery import discover_plugins

console = Console()


def version() -> None:
    """Display version information."""
    try:
        checkup_version = pkg_version("checkup")
    except Exception:
        checkup_version = "unknown"

    console.print(f"checkup {checkup_version}")
    console.print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    plugins = discover_plugins()
    if plugins:
        console.print("Installed plugins:")
        for plugin in plugins:
            console.print(f"  {plugin['name']} {plugin['version']}")
