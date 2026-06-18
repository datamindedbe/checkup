"""
Plugin registry for discovering providers, metrics, and materializers.
"""

from checkup.registry.discovery import (
    Plugin,
    PluginRegistry,
    get_registry,
)

__all__ = [
    "Plugin",
    "PluginRegistry",
    "get_registry",
]
