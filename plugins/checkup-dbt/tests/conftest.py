from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from checkup_dbt import DbtModelsNotAdheringToNamingConventionMetric

from checkup.types import Context


@pytest.fixture
def sample_dbt_project_dir() -> Path:
    return Path(__file__).parent / "fixtures" / "sample_dbt_project"


@pytest.fixture
def sample_manifest_path(sample_dbt_project_dir: Path) -> Path:
    return sample_dbt_project_dir / "target" / "manifest.json"


@pytest.fixture
def sample_manifest_path_with_git_packages(
    sample_dbt_project_dir: Path,
) -> Generator[Path, None, None]:
    """Fixture that temporarily adds git packages to packages.yml for testing."""
    packages_path = sample_dbt_project_dir / "packages.yml"
    original_content = packages_path.read_text() if packages_path.exists() else None

    packages_with_git = """\
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
  - git: https://github.com/example/flagged-package
    revision: main
  - git: https://github.com/example/safe-package
    revision: v1.0.0
"""
    packages_path.write_text(packages_with_git)

    yield sample_dbt_project_dir / "target" / "manifest.json"

    if original_content is not None:
        packages_path.write_text(original_content)
    else:
        packages_path.unlink()


def internal_model_naming_checker(context: Context, model: Any) -> bool:
    if not model.schema.endswith("__int"):
        return True
    alias = getattr(model, "alias", None)
    if alias is None:
        return True
    return alias.startswith("stg_") or alias.startswith("int_")


class InternalModelNamingMetric(DbtModelsNotAdheringToNamingConventionMetric):
    @classmethod
    def get_checker(cls):
        return internal_model_naming_checker


def fact_dim_naming_checker(context: Context, model: Any) -> bool:
    return model.name.startswith("fact_") or model.name.startswith("dim_")


class FactDimNamingMetric(DbtModelsNotAdheringToNamingConventionMetric):
    @classmethod
    def get_checker(cls):
        return fact_dim_naming_checker
