from pathlib import Path

from checkup_dbt import (
    DbtColumnTestCoverageMetric,
    DbtColumnTestsMetric,
    DbtDataTestsMetric,
    DbtTestedColumnsMetric,
    DbtUnitTestsMetric,
)
from checkup_dbt.provider import DbtManifestProvider

from checkup.hub import CheckHub


def test_unit_tests_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtUnitTestsMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_unit_tests"
    assert measurement.value == 1


def test_data_tests_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtDataTestsMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_data_tests"
    assert measurement.value == 8


def test_column_tests_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtColumnTestsMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_column_tests"
    assert measurement.value == 8


def test_tested_columns_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtTestedColumnsMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    measurement = result.measurements[0]
    assert measurement.metric.name == "dbt_tested_columns"
    assert measurement.value == 5


def test_column_test_coverage_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtColumnTestCoverageMetric()])
        .with_providers([[DbtManifestProvider(manifest_path=sample_manifest_path)]])
        .measure()
    )

    assert len(result.measurements) == 3

    coverage_measurement = next(
        m for m in result.measurements if m.metric.name == "dbt_column_test_coverage"
    )
    assert coverage_measurement.metric.unit == "percent"
    assert coverage_measurement.value == 41
