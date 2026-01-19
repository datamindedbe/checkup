"""Module loader for checkup Python files."""

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from checkup.hub import CheckUp


class LoadError(Exception):
    """Error loading a checkup module."""

    pass


def load_checkup(path: Path) -> "CheckUp":
    """Load a CheckUp instance from a Python file.

    The module must define a 'hub' variable containing a CheckUp instance.

    Args:
        path: Path to the Python file

    Returns:
        The CheckUp instance from the module

    Raises:
        LoadError: If the file cannot be loaded or doesn't contain a hub
    """
    if not path.exists():
        raise LoadError(f"File not found: {path}")

    if not path.suffix == ".py":
        raise LoadError(f"Not a Python file: {path}")

    # Load the module
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise LoadError(f"Cannot load module spec from: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise LoadError(f"Error executing module {path}: {e}") from e

    # Look for 'hub' variable
    if hasattr(module, "hub"):
        hub = module.hub
        from checkup.hub import CheckUp

        if isinstance(hub, CheckUp):
            return hub
        raise LoadError(
            f"'hub' in {path} is not a CheckUp instance (got {type(hub).__name__})"
        )

    raise LoadError(f"No 'hub' variable found in {path}")
