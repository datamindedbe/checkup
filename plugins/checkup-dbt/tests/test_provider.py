from pathlib import Path

from checkup.hub import CheckHub
from checkup_dbt import DbtModelsMetric


def test_manifest_path_mode(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].value == 3


def test_dbt_project_dir_mode(sample_dbt_project_dir: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .measure(
            initial_context={
                "dbt_project_dir": str(sample_dbt_project_dir),
                "profiles_dir": str(sample_dbt_project_dir),
            }
        )
    )

    assert len(result.metrics) == 1
    assert result.metrics[0].value == 3


def test_missing_context_raises_error():
    result = CheckHub().with_metrics([DbtModelsMetric]).measure(initial_context={})

    assert len(result.errors) == 1
    assert "manifest_path" in str(result.errors[0][1])


def test_multiple_projects(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .with_contexts(
            [
                {"manifest_path": str(sample_manifest_path), "project": "project_a"},
                {"manifest_path": str(sample_manifest_path), "project": "project_b"},
            ]
        )
        .measure()
    )

    assert len(result.metrics) == 2
    assert all(m.value == 3 for m in result.metrics)
    projects = {m.tags["project"] for m in result.metrics}
    assert projects == {"project_a", "project_b"}
