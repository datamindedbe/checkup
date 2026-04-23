"""
Plugin registry for discovering providers, metrics, and materializers.
"""

from checkup.registry.discovery import (
    PluginRegistry,
    get_registry,
)

__all__ = [
    "PluginRegistry",
    "get_registry",
]
