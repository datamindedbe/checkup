# dbt Metrics Plugin Design

## Overview

Implement a checkup plugin for dbt metrics, porting 16 metrics from the reference implementation to the checkup framework.

## Architecture

```
plugins/checkup-dbt/
├── pyproject.toml              # Add dbt-core dependency
└── src/checkup_dbt/
    ├── __init__.py             # Exports all metrics + provider
    ├── provider.py             # Manifest loading (both modes)
    └── metrics.py              # All 16 metric classes
```

## Provider

A single `dbt_manifest_provider` function enriches context with parsed manifest:

- If `manifest_path` in context → loads JSON directly
- If `dbt_project_dir` in context → runs `dbt deps` + `dbt parse`
- Stores result as `context["dbt_manifest"]`

The `DbtMetric` base class declares this provider, so all dbt metrics automatically get the manifest.

## Metrics

| Metric Class | Name | Unit | Dependencies |
|--------------|------|------|--------------|
| **Core Counts** |
| DbtModelsMetric | dbt_models | models | - |
| DbtColumnsMetric | dbt_columns | columns | - |
| DbtTestsMetric | dbt_tests | tests | - |
| DbtModelsWithDescriptionMetric | dbt_models_with_description | models | - |
| DbtColumnsWithDescriptionMetric | dbt_columns_with_description | columns | - |
| **Test Types** |
| DbtUnitTestsMetric | dbt_unit_tests | tests | - |
| DbtDataTestsMetric | dbt_data_tests | tests | - |
| DbtColumnTestsMetric | dbt_column_tests | tests | - |
| DbtTestedColumnsMetric | dbt_tested_columns | columns | - |
| DbtColumnTestCoverageMetric | dbt_column_test_coverage | percent | DbtTestedColumnsMetric, DbtColumnsMetric |
| **Output Models** |
| DbtOutputModelsMetric | dbt_output_models | models | - |
| DbtOutputModelsWithDescriptionMetric | dbt_output_models_with_description | models | - |
| DbtOutputModelsWithoutContractsMetric | dbt_output_models_without_contracts | models | - |
| DbtOutputColumnsWithoutDataTypeMetric | dbt_output_columns_without_data_type | columns | - |
| **Quality** |
| DbtInternalModelsWithWrongPrefixMetric | dbt_internal_models_wrong_prefix | models | - |
| DbtSupportedVersionMetric | dbt_supported_version | boolean | - (configurable) |

## Configuration

`DbtSupportedVersionMetric` has a configurable `expected_version` field (default: "1.9") that can be overridden via YAML config.

## Usage

```python
# With pre-generated manifest
CheckHub().with_metrics([DbtModelsMetric]).measure(
    initial_context={"manifest_path": "/path/to/manifest.json"}
)

# With live parsing
CheckHub().with_metrics([DbtModelsMetric]).measure(
    initial_context={"dbt_project_dir": "/path/to/dbt/project"}
)

# Multi-project with tags
CheckHub().with_metrics([DbtModelsMetric]).with_contexts([
    {"manifest_path": "/proj1/manifest.json", "product": "proj1"},
    {"manifest_path": "/proj2/manifest.json", "product": "proj2"},
]).measure()
```
