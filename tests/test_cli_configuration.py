"""
Tests for CLI configuration loading and parsing.
"""

import yaml

from checkup.cli.utils import parse_cli_item
from checkup.configuration.env import (
    apply_naming_convention_overrides,
    substitute_env_vars,
)
from checkup.configuration.io import (
    load_config,
    merge_configs,
    parse_materializer,
    parse_metrics,
    parse_providers,
)
from checkup.configuration.models import CheckupConfig


class TestParseProviders:
    def test_string_shorthand_creates_provider_with_empty_config(self):
        raw = ["git", "dbt"]
        result = parse_providers(raw)

        assert len(result) == 2
        assert result[0].name == "git"
        assert result[0].config == {}
        assert result[1].name == "dbt"

    def test_dict_with_name_field_extracts_config(self):
        raw = [
            {"name": "git", "repo_path": "/path/to/repo"},
            {"name": "dbt", "project_dir": "./dbt", "profiles_dir": "~/.dbt"},
        ]
        result = parse_providers(raw)

        assert len(result) == 2
        assert result[0].name == "git"
        assert result[0].config == {"repo_path": "/path/to/repo"}
        assert result[1].name == "dbt"
        assert result[1].config == {"project_dir": "./dbt", "profiles_dir": "~/.dbt"}

    def test_mixed_string_and_dict_formats(self):
        raw = [
            "git",
            {"name": "dbt", "project_dir": "./dbt"},
        ]
        result = parse_providers(raw)

        assert len(result) == 2
        assert result[0].name == "git"
        assert result[0].config == {}
        assert result[1].name == "dbt"
        assert result[1].config == {"project_dir": "./dbt"}

    def test_empty_list_returns_empty(self):
        assert parse_providers([]) == []
        assert parse_providers(None) == []


class TestParseMetrics:
    def test_string_shorthand_is_ignored(self):
        raw = ["git_days_since_last_update", "python_version"]
        result = parse_metrics(raw)

        assert len(result) == 0

    def test_dict_with_type_field_extracts_config(self):
        raw = [
            {
                "type": "python_version_check",
                "min_version": "3.10",
                "max_version": "3.13",
            },
        ]
        result = parse_metrics(raw)

        assert len(result) == 1
        assert result[0].type == "python_version_check"
        assert result[0].name is None
        assert result[0].config == {"min_version": "3.10", "max_version": "3.13"}

    def test_dict_with_type_and_name_for_multiple_instances(self):
        raw = [
            {
                "type": "git_tracked_file_count",
                "name": "readme_exists",
                "pattern": "README.md",
            },
            {
                "type": "git_tracked_file_count",
                "name": "license_exists",
                "pattern": "LICENSE",
            },
        ]
        result = parse_metrics(raw)

        assert [(m.type, m.name) for m in result] == [
            ("git_tracked_file_count", "readme_exists"),
            ("git_tracked_file_count", "license_exists"),
        ]


class TestParseMaterializer:
    def test_extracts_type_and_remaining_fields_as_config(self):
        raw = {"type": "console", "group_tag_1": "product", "group_tag_2": "team"}
        result = parse_materializer(raw)

        assert result.type == "console"
        assert result.config == {"group_tag_1": "product", "group_tag_2": "team"}

    def test_returns_none_when_type_missing(self):
        assert parse_materializer({"group_tag_1": "product"}) is None
        assert parse_materializer(None) is None


class TestMergeConfigs:
    def test_child_tags_merged_with_parent(self):
        parent = {"tags": {"team": "platform", "env": "prod"}}
        child = {"tags": {"product": "my-product"}}

        result = merge_configs(parent, child)

        assert result["tags"] == {
            "team": "platform",
            "env": "prod",
            "product": "my-product",
        }

    def test_child_tag_overrides_parent(self):
        parent = {"tags": {"env": "prod"}}
        child = {"tags": {"env": "dev"}}

        result = merge_configs(parent, child)

        assert result["tags"]["env"] == "dev"

    def test_child_providers_replace_parent(self):
        parent = {"providers": [{"name": "git"}]}
        child = {"providers": [{"name": "dbt"}]}

        result = merge_configs(parent, child)

        assert result["providers"] == [{"name": "dbt"}]

    def test_child_materializer_replaces_parent(self):
        parent = {"materializer": {"type": "csv"}}
        child = {"materializer": {"type": "console"}}

        result = merge_configs(parent, child)

        assert result["materializer"]["type"] == "console"


class TestSubstituteEnvVars:
    def test_substitutes_env_var_reference(self, monkeypatch):
        monkeypatch.setenv("MY_VAR", "secret_value")
        config = {"password": "${MY_VAR}"}

        result = substitute_env_vars(config)

        assert result["password"] == "secret_value"

    def test_uses_default_when_var_not_set(self):
        config = {"timeout": "${MISSING_VAR:-30}"}

        result = substitute_env_vars(config)

        assert result["timeout"] == "30"

    def test_leaves_unset_var_without_default_unchanged(self):
        """Unset vars without defaults are left as-is (with warning logged)."""
        config = {"value": "${DEFINITELY_NOT_SET}"}

        result = substitute_env_vars(config)

        assert result["value"] == "${DEFINITELY_NOT_SET}"

    def test_substitutes_in_nested_structures(self, monkeypatch):
        monkeypatch.setenv("DB_HOST", "localhost")
        config = {
            "providers": [
                {"name": "db", "host": "${DB_HOST}"},
            ]
        }

        result = substitute_env_vars(config)

        assert result["providers"][0]["host"] == "localhost"


class TestNamingConventionOverrides:
    def test_materializer_override_applied_when_type_matches(self, monkeypatch):
        monkeypatch.setenv(
            "CHECKUP__MATERIALIZER__SQLALCHEMY__CONNECTION_URL",
            "postgresql://localhost",
        )
        config = {"materializer": {"type": "sqlalchemy"}}

        result = apply_naming_convention_overrides(config)

        assert result["materializer"]["connection_url"] == "postgresql://localhost"

    def test_materializer_override_skipped_when_type_differs(self, monkeypatch):
        monkeypatch.setenv(
            "CHECKUP__MATERIALIZER__SQLALCHEMY__CONNECTION_URL",
            "postgresql://localhost",
        )
        config = {"materializer": {"type": "console"}}

        result = apply_naming_convention_overrides(config)

        assert "connection_url" not in result["materializer"]

    def test_explicit_config_wins_over_naming_convention(self, monkeypatch):
        monkeypatch.setenv(
            "CHECKUP__MATERIALIZER__SQLALCHEMY__CONNECTION_URL", "env-url"
        )
        config = {"materializer": {"type": "sqlalchemy", "connection_url": "yaml-url"}}

        result = apply_naming_convention_overrides(config)

        assert result["materializer"]["connection_url"] == "yaml-url"

    def test_malformed_materializer_env_var_logs_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("CHECKUP__MATERIALIZER__SQLALCHEMY", "value")
        config = {"materializer": {"type": "sqlalchemy"}}

        apply_naming_convention_overrides(config)

        assert "malformed" in caplog.text.lower()
        assert "CHECKUP__MATERIALIZER__SQLALCHEMY" in caplog.text

    def test_malformed_provider_env_var_logs_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("CHECKUP__PROVIDER__GIT", "value")
        config = {"providers": [{"name": "git"}]}

        apply_naming_convention_overrides(config)

        assert "malformed" in caplog.text.lower()
        assert "CHECKUP__PROVIDER__GIT" in caplog.text


class TestLoadConfig:
    def test_loads_yaml_file(self, tmp_path):
        config_file = tmp_path / "checkup.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "tags": {"product": "test"},
                    "providers": [{"name": "git"}],
                    "metrics": [{"type": "dummy_metric"}],
                }
            )
        )

        result = load_config(config_path=config_file)

        assert isinstance(result, CheckupConfig)
        assert result.tags == {"product": "test"}
        assert len(result.providers) == 1
        assert result.providers[0].name == "git"

    def test_returns_empty_config_when_no_file_found(self, tmp_path):
        result = load_config(start_dir=tmp_path)

        assert result.tags == {}
        assert result.providers == []
        assert result.metrics == []

    def test_hierarchical_loading_merges_parent_and_child(self, tmp_path):
        # Create parent directory with config
        parent_dir = tmp_path / "parent"
        parent_dir.mkdir()
        (parent_dir / "checkup.yaml").write_text(
            yaml.dump({"tags": {"team": "platform"}})
        )

        # Create child directory with config
        child_dir = parent_dir / "child"
        child_dir.mkdir()
        (child_dir / "checkup.yaml").write_text(
            yaml.dump({"tags": {"product": "my-product"}})
        )

        result = load_config(start_dir=child_dir)

        assert result.tags == {"team": "platform", "product": "my-product"}


class TestParseCliItem:
    def test_name_only(self):
        name, config = parse_cli_item("git")

        assert name == "git"
        assert config == {}

    def test_empty_config(self):
        name, config = parse_cli_item("git:")

        assert name == "git"
        assert config == {}

    def test_name_with_config_pairs(self):
        name, config = parse_cli_item("dbt:project_dir=./dbt,profiles_dir=~/.dbt")

        assert name == "dbt"
        assert config == {"project_dir": "./dbt", "profiles_dir": "~/.dbt"}

    def test_value_containing_special_characters(self):
        name, config = parse_cli_item("db:url=postgres://host:5432,user=name=admin")

        assert name == "db"
        assert config == {"url": "postgres://host:5432", "user": "name=admin"}

    def test_malformed_pair_is_skipped(self, caplog):
        name, config = parse_cli_item("dbt:project_dir=./dbt,malformed,other=value")

        assert name == "dbt"
        assert config == {"project_dir": "./dbt", "other": "value"}
        assert "malformed" in caplog.text
