from pathlib import Path

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
    DbtVersionMetric,
)
from checkup_dbt.provider import DbtManifestProvider

from checkup.hub import CheckHub

from .conftest import InternalModelNamingMetric


class Dbt19SupportedVersionMetric(DbtSupportedVersionMetric):
    min_version: str = "1.9"


def test_all_metrics(sample_manifest_path: Path):
    all_metrics = [
        DbtModelsMetric(),
        DbtColumnsMetric(),
        DbtTestsMetric(),
        DbtModelsWithDescriptionMetric(),
        DbtColumnsWithDescriptionMetric(),
        DbtUnitTestsMetric(),
        DbtDataTestsMetric(),
        DbtColumnTestsMetric(),
        DbtTestedColumnsMetric(),
        DbtColumnTestCoverageMetric(),
        DbtOutputModelsMetric(),
        DbtOutputModelsWithDescriptionMetric(),
        DbtOutputModelsWithoutContractsMetric(),
        DbtOutputColumnsWithoutDataTypeMetric(),
        InternalModelNamingMetric(),
        Dbt19SupportedVersionMetric(),
        DbtVersionMetric(),
    ]

    result = (
        CheckHub()
        .with_metrics(all_metrics)
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    assert len(result.measurements) == 17
    assert len(result.errors) == 0

    for measurement in result.measurements:
        assert measurement.value is not None, f"{measurement.metric.name} has no value"
