from pathlib import Path

from checkup.hub import CheckHub
from checkup_dbt import (
    DbtColumnsMetric,
    DbtColumnsWithDescriptionMetric,
    DbtModelsMetric,
    DbtModelsWithDescriptionMetric,
    DbtTestsMetric,
)


def test_models_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_models"
    assert metric.value == 3


def test_columns_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtColumnsMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_columns"
    assert metric.value == 12


def test_tests_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtTestsMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_tests"
    assert metric.value == 9


def test_models_with_description_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtModelsWithDescriptionMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_models_with_description"
    assert metric.value == 3


def test_columns_with_description_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtColumnsWithDescriptionMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_columns_with_description"
    assert metric.value == 10
