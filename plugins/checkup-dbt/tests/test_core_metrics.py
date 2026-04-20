from pathlib import Path

from checkup_dbt import (
    DbtColumnsMetric,
    DbtColumnsWithDescriptionMetric,
    DbtColumnsWithoutDescriptionMetric,
    DbtModelsMetric,
    DbtModelsWithDescriptionMetric,
    DbtModelsWithoutDescriptionMetric,
    DbtTestsMetric,
)
from checkup_dbt.provider import DbtManifestProvider

from checkup.hub import CheckHub


def test_models_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_models"
    assert measurement.value == 3


def test_columns_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtColumnsMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_columns"
    assert measurement.value == 12


def test_tests_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtTestsMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_tests"
    assert measurement.value == 9


def test_models_with_description_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsWithDescriptionMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_models_with_description"
    assert measurement.value == 3


def test_columns_with_description_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtColumnsWithDescriptionMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_columns_with_description"
    assert measurement.value == 10


def test_models_without_description_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsWithoutDescriptionMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_models_without_description"
    assert measurement.value == 0  # All 3 models have descriptions


def test_columns_without_description_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtColumnsWithoutDescriptionMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_columns_without_description"
    assert measurement.value == 2  # 12 total - 10 with descriptions = 2 without
