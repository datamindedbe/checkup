import os
from pathlib import Path

import pytest
from checkup_python.provider import PythonProvider


@pytest.fixture
def uv_project_dir() -> str:
    return str(Path(__file__).parent / "fixtures" / "uv-project")


@pytest.fixture
def non_uv_project_dir() -> str:
    return str(Path(__file__).parent / "fixtures" / "non-uv-project")


def test_provider_name():
    provider = PythonProvider(dir="/tmp/test")
    assert provider.name == "python"


def test_is_uv_project_returns_true_for_uv_project(uv_project_dir):
    """Test that _is_uv_project correctly identifies uv projects."""
    provider = PythonProvider(dir=uv_project_dir)
    assert provider._is_uv_project() is True


def test_is_uv_project_returns_false_for_non_uv_project(non_uv_project_dir):
    """Test that _is_uv_project correctly identifies non-uv projects."""
    provider = PythonProvider(dir=non_uv_project_dir)
    assert provider._is_uv_project() is False


def test_non_uv_project_skipped(non_uv_project_dir):
    """Test that non-uv projects are skipped and not installed."""
    provider = PythonProvider(dir=non_uv_project_dir)
    result = provider.provide()

    # Should not be installed since it's not a uv project
    assert result["installed"] is False

    # Verify the directory exists and has setup.py
    assert os.path.exists(non_uv_project_dir)
    assert os.path.exists(os.path.join(non_uv_project_dir, "setup.py"))
