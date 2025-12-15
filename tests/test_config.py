"""Tests for YAML configuration loading."""
from pathlib import Path

from checkup.config import load_config


def test_load_config(tmp_path):
    """Test loading metric configs from YAML."""
    # Create test YAML
    config_file = tmp_path / "checkup.yaml"
    config_file.write_text("""
metrics:
  dummy:
    expected_value: 100
  python_version:
    min: "3.11.0"
    max: "3.12.99"
""")

    config = load_config(config_file)

    assert "dummy" in config
    assert config["dummy"]["expected_value"] == 100
    assert config["python_version"]["min"] == "3.11.0"


def test_load_config_missing_file():
    """Test loading config when file doesn't exist."""
    config = load_config(Path("nonexistent.yaml"))

    assert config == {}


def test_load_config_empty_file(tmp_path):
    """Test loading config from empty YAML file."""
    config_file = tmp_path / "checkup.yaml"
    config_file.write_text("")

    config = load_config(config_file)

    assert config == {}


def test_load_config_no_metrics_key(tmp_path):
    """Test loading config without metrics key."""
    config_file = tmp_path / "checkup.yaml"
    config_file.write_text("other_key: value")

    config = load_config(config_file)

    assert config == {}
