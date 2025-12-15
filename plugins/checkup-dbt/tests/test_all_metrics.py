from pathlib import Path

from checkup.hub import CheckHub
from checkup_dbt import (
    DbtColumnsMetric,
    DbtColumnsWithDescriptionMetric,
    DbtColumnTestCoverageMetric,
    DbtColumnTestsMetric,
    DbtDataTestsMetric,
    DbtModelsMetric,
    DbtModelsWithDescriptionMetric,
    DbtOutputColumnsWithoutDataTypeMetric,
    DbtOutputModelsMetric,
    DbtOutputModelsWithDescriptionMetric,
    DbtOutputModelsWithoutContractsMetric,
    DbtSupportedVersionMetric,
    DbtTestedColumnsMetric,
    DbtTestsMetric,
    DbtUnitTestsMetric,
)

from .conftest import InternalModelNamingMetric


def test_all_metrics(sample_manifest_path: Path):
    all_metrics = [
        DbtModelsMetric,
        DbtColumnsMetric,
        DbtTestsMetric,
        DbtModelsWithDescriptionMetric,
        DbtColumnsWithDescriptionMetric,
        DbtUnitTestsMetric,
        DbtDataTestsMetric,
        DbtColumnTestsMetric,
        DbtTestedColumnsMetric,
        DbtColumnTestCoverageMetric,
        DbtOutputModelsMetric,
        DbtOutputModelsWithDescriptionMetric,
        DbtOutputModelsWithoutContractsMetric,
        DbtOutputColumnsWithoutDataTypeMetric,
        InternalModelNamingMetric,
        DbtSupportedVersionMetric,
    ]

    result = (
        CheckHub()
        .with_metrics(all_metrics)
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    assert len(result.metrics) == 16
    assert len(result.errors) == 0

    for metric in result.metrics:
        assert metric.value is not None, f"{metric.name} has no value"
