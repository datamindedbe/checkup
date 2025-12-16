from pathlib import Path

from checkup.hub import CheckHub
from checkup_dbt import (
    DbtOutputColumnsWithoutDataTypeMetric,
    DbtOutputModelsMetric,
    DbtOutputModelsWithDescriptionMetric,
    DbtOutputModelsWithoutContractsMetric,
)
from checkup_dbt.provider import DbtManifestProvider


def test_output_models_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtOutputModelsMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_output_models"
    assert metric.value == 1


def test_output_models_with_description_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtOutputModelsWithDescriptionMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_output_models_with_description"
    assert metric.value == 1


def test_output_models_without_contracts_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtOutputModelsWithoutContractsMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_output_models_without_contracts"
    assert metric.value == 0


def test_output_columns_without_data_type_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtOutputColumnsWithoutDataTypeMetric])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_output_columns_without_data_type"
    assert metric.value == 0
