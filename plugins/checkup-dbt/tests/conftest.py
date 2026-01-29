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
