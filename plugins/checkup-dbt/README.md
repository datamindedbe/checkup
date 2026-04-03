# checkup-dbt

dbt metrics plugin for [checkup](https://pypi.org/project/checkup/).

## Installation

```bash
pip install checkup-dbt
```

## Requirements

- Python >= 3.12
- [checkup](https://pypi.org/project/checkup/)
- dbt-core >= 1.9

## Usage

```python
from checkup import CheckHub
from checkup_dbt import (
    DbtManifestProvider,
    DbtModelsMetric,
    DbtColumnsMetric,
    DbtTestsMetric,
)

results = (
    CheckHub()
    .with_metrics([
        DbtModelsMetric(),
        DbtColumnsMetric(),
        DbtTestsMetric(),
    ])
    .with_providers([[
        DbtManifestProvider(dbt_project_dir="./my_dbt_project"),
    ]])
    .measure()
)
```

## Provider

### DbtManifestProvider

Provides dbt manifest data to metrics. Can either parse a dbt project directory or load a pre-generated manifest file.

## Available Metrics

### Core Metrics

#### DbtModelsMetric

Total number of dbt models.

#### DbtColumnsMetric

Total number of columns across all models.

#### DbtTestsMetric

Total number of tests.

#### DbtModelsWithDescriptionMetric

Number of models that have descriptions.

#### DbtModelsWithoutDescriptionMetric

Number of models missing descriptions.

#### DbtColumnsWithDescriptionMetric

Number of columns that have descriptions.

#### DbtColumnsWithoutDescriptionMetric

Number of columns missing descriptions.

### Test Metrics

#### DbtUnitTestsMetric

Number of unit tests.

#### DbtDataTestsMetric

Number of data tests.

#### DbtColumnTestsMetric

Number of column-level tests.

#### DbtTestedColumnsMetric

Number of columns that have at least one test.

#### DbtColumnTestCoverageMetric

Percentage of columns with tests.

### Output Model Metrics

#### DbtOutputModelsMetric

Number of models exposed as outputs.

#### DbtOutputModelsWithDescriptionMetric

Number of output models with descriptions.

#### DbtOutputModelsWithoutDescriptionMetric

Number of output models missing descriptions.

#### DbtOutputModelsWithoutContractsMetric

Number of output models without contracts.

#### DbtOutputColumnsWithoutDataTypeMetric

Number of output columns without data types.

### Quality Metrics

#### DbtModelsNotAdheringToNamingConventionMetric

Number of models not following naming conventions.

#### DbtVersionMetric

Current dbt version.

#### DbtSupportedVersionMetric

Whether dbt version is supported. Configure by subclassing:

```python
from checkup_dbt import DbtSupportedVersionMetric

class MySupportedVersionMetric(DbtSupportedVersionMetric):
    min_version = "1.9"
```

#### DbtFlaggedPackagesMetric

Packages flagged for review. Configure by subclassing:

```python
from checkup_dbt import DbtFlaggedPackagesMetric

class MyFlaggedPackagesMetric(DbtFlaggedPackagesMetric):
    flagged_packages = [
        "https://github.com/example/deprecated-package",
    ]
```

#### DbtProfileHostMetric

Profile host configuration.

## Creating Custom Metrics

Extend `DbtMetric` to create custom dbt-based metrics:

```python
from checkup_dbt import DbtMetric

class MyCustomDbtMetric(DbtMetric):
    name = "my_custom_metric"
    description = "My custom dbt metric"

    def calculate(self, context, measurements):
        manifest = self.get_manifest(context)
        return self.measurement(value=len(manifest.nodes))
```
