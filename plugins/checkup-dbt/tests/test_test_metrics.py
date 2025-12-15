from pathlib import Path

from checkup.hub import CheckHub
from checkup_dbt import (
    DbtColumnTestCoverageMetric,
    DbtColumnTestsMetric,
    DbtDataTestsMetric,
    DbtTestedColumnsMetric,
    DbtUnitTestsMetric,
)


def test_unit_tests_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtUnitTestsMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_unit_tests"
    assert metric.value == 1


def test_data_tests_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtDataTestsMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_data_tests"
    assert metric.value == 8


def test_column_tests_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtColumnTestsMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_column_tests"
    assert metric.value == 8


def test_tested_columns_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtTestedColumnsMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    metric = result.metrics[0]
    assert metric.name == "dbt_tested_columns"
    assert metric.value == 5


def test_column_test_coverage_metric(sample_manifest_path: Path):
    result = (
        CheckHub()
        .with_metrics([DbtColumnTestCoverageMetric])
        .measure(initial_context={"manifest_path": str(sample_manifest_path)})
    )

    assert len(result.metrics) == 3

    coverage_metric = next(
        m for m in result.metrics if m.name == "dbt_column_test_coverage"
    )
    assert coverage_metric.unit == "percent"
    assert coverage_metric.value == 41
