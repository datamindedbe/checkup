"""
Tests for the `checkup plugins` CLI command.
"""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from checkup.cli import app
from checkup.registry.discovery import Plugin, PluginRegistry


def _make_entrypoint(name: str, dist_name: str, dist_version: str) -> MagicMock:
    """
    Mock `importlib.metadata.EntryPoint`.
    """

    ep = MagicMock()
    ep.name = name
    ep.dist = MagicMock(name=dist_name, version=dist_version)
    ep.dist.name = dist_name
    ep.dist.version = dist_version
    return ep


class TestListPlugins:
    def test_groups_entry_points_by_distribution(self):
        registry = PluginRegistry()

        def fake_entry_points(group: str):
            match group:
                case "checkup.providers":
                    return [_make_entrypoint("git", "checkup-git", "1.0.0")]
                case "checkup.metrics":
                    return [
                        _make_entrypoint("git_count", "checkup-git", "1.0.0"),
                        _make_entrypoint("python_version", "checkup-python", "2.0.0"),
                    ]
                case "checkup.materializers":
                    return [_make_entrypoint("console", "checkup", "0.5.0")]
                case _:
                    return []

        with patch(
            "checkup.registry.discovery.entry_points", side_effect=fake_entry_points
        ):
            plugins = registry.list_plugins()

        assert set(plugins) == {"checkup-git", "checkup-python", "checkup"}
        assert plugins["checkup-git"] == Plugin(
            version="1.0.0",
            providers=["git"],
            metrics=["git_count"],
        )
        assert plugins["checkup-python"].metrics == ["python_version"]
        assert plugins["checkup"].materializers == ["console"]


class TestPluginsCommand:
    def test_renders_plugin_table_excluding_core(self):
        runner = CliRunner()

        fake_plugins = {
            "checkup": Plugin(version="0.5.0", materializers=["console"]),
            "checkup-git": Plugin(
                version="1.2.3", providers=["git"], metrics=["git_count"]
            ),
        }

        with patch("checkup.cli.commands.plugins.get_registry") as mock_get_registry:
            mock_get_registry.return_value.list_plugins.return_value = fake_plugins
            result = runner.invoke(app, ["plugins"])

        assert result.exit_code == 0
        assert "checkup-git" in result.stdout
        assert "1.2.3" in result.stdout
        assert "git_count" in result.stdout
