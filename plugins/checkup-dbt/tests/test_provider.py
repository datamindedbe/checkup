from pathlib import Path

import pytest

from checkup.hub import CheckHub
from checkup.providers.tags import TagProvider
from checkup_dbt import DbtModelsMetric
from checkup_dbt.provider import DbtManifestProvider


def test_manifest_path_mode(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].value == 3


def test_dbt_project_dir_mode(sample_dbt_project_dir: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .with_providers([[
            DbtManifestProvider(
                dbt_project_dir=sample_dbt_project_dir,
                profiles_dir=sample_dbt_project_dir,
            )
        ]])
        .measure()
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].value == 3


def test_missing_args_raises_error():
    with pytest.raises(ValueError) as exc_info:
        DbtManifestProvider()

    assert "manifest_path" in str(exc_info.value) or "dbt_project_dir" in str(exc_info.value)


def test_multiple_projects(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .with_providers([
            [DbtManifestProvider(manifest_path=sample_manifest_path), TagProvider(project="project_a")],
            [DbtManifestProvider(manifest_path=sample_manifest_path), TagProvider(project="project_b")],
        ])
        .measure()
    )

    assert len(result.metrics) == 2
    assert all(m.value == 3 for m in result.metrics)
    projects = {m.tags["project"] for m in result.metrics}
    assert projects == {"project_a", "project_b"}
