from pathlib import Path

from checkup.hub import CheckHub
from checkup_dbt import DbtSupportedVersionMetric

from .conftest import FactDimNamingMetric, InternalModelNamingMetric


def test_naming_convention_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([InternalModelNamingMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_models_not_adhering_to_naming_convention"
    assert metric.value == 0


def test_naming_convention_metric_custom_checker(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([FactDimNamingMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    assert len(result.errors) == 0, f"Errors: {result.errors}"
    assert len(result.metrics) == 1

    metric = result.metrics[0]
    assert metric.value == 3


def test_supported_version_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtSupportedVersionMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_supported_version"
    assert metric.unit == "boolean"
    assert metric.value == 1
