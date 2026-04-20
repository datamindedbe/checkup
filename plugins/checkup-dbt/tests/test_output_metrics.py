from pathlib import Path

from checkup_dbt import (
    DbtOutputColumnsWithoutDataTypeMetric,
    DbtOutputModelsMetric,
    DbtOutputModelsWithDescriptionMetric,
    DbtOutputModelsWithoutContractsMetric,
    DbtOutputModelsWithoutDescriptionMetric,
)
from checkup_dbt.provider import DbtManifestProvider

from checkup.hub import CheckHub


def test_output_models_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtOutputModelsMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_output_models"
    assert measurement.value == 1


def test_output_models_with_description_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtOutputModelsWithDescriptionMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_output_models_with_description"
    assert measurement.value == 1


def test_output_models_without_description_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtOutputModelsWithoutDescriptionMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_output_models_without_description"
    assert measurement.value == 0  # The 1 output model has a description


def test_output_models_without_contracts_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtOutputModelsWithoutContractsMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_output_models_without_contracts"
    assert measurement.value == 0


def test_output_columns_without_data_type_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtOutputColumnsWithoutDataTypeMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_output_columns_without_data_type"
    assert measurement.value == 0
