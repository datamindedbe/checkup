# dbt Plugin

The dbt plugin provides metrics for analyzing dbt (data build tool) projects.

## Installation

```bash
pip install checkup-dbt
```

**Note:** This plugin requires `dbt-core>=1.9`.

## Provider

### DbtProvider

Fetches dbt project information including models, tests, and documentation.

```python
from checkup_dbt import DbtProvider

provider = DbtProvider(project_path="/path/to/dbt/project")
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_path` | `str` or `Path` | Yes | Path to the dbt project directory |
| `profiles_dir` | `str` or `Path` | No | Path to profiles directory |
| `target` | `str` | No | dbt target to use |

**Context Data:**

The provider adds the following data under the `dbt` namespace:

```python
context["dbt"] = {
    "models": [...],          # List of dbt models
    "tests": [...],           # List of dbt tests
    "sources": [...],         # List of dbt sources
    "macros": [...],          # List of dbt macros
    "manifest": {...},        # Parsed manifest.json
    "project_name": "...",    # Project name from dbt_project.yml
}
```

## Metrics

### ModelCountMetric

Counts the total number of dbt models.

```python
from checkup_dbt import ModelCountMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `dbt_model_count` |
| Unit | `models` |
| Dependencies | None |
| Providers | `DbtProvider` |

### ModelTestCoverageMetric

Calculates the percentage of models with at least one test.

```python
from checkup_dbt import ModelTestCoverageMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `dbt_test_coverage` |
| Unit | `percent` |
| Dependencies | `ModelCountMetric` |
| Providers | `DbtProvider` |

### ModelDocumentationMetric

Calculates the percentage of models with documentation.

```python
from checkup_dbt import ModelDocumentationMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `dbt_doc_coverage` |
| Unit | `percent` |
| Dependencies | `ModelCountMetric` |
| Providers | `DbtProvider` |

### SourceFreshnessMetric

Checks source freshness configuration coverage.

```python
from checkup_dbt import SourceFreshnessMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `dbt_source_freshness` |
| Unit | `percent` |
| Dependencies | None |
| Providers | `DbtProvider` |

## Example Usage

```python
from checkup import CheckHub, HTMLMaterializer
from checkup_dbt import (
    DbtProvider,
    ModelCountMetric,
    ModelTestCoverageMetric,
    ModelDocumentationMetric,
)
from pathlib import Path

result = (
    CheckHub()
    .with_metrics([
        ModelCountMetric,
        ModelTestCoverageMetric,
        ModelDocumentationMetric,
    ])
    .with_providers([
        [DbtProvider(project_path="./analytics")],
    ])
    .measure()
)

result.materialize(
    HTMLMaterializer(
        output_path=Path("dbt_report.html"),
        group_tag_1="project",
        group_tag_2="layer"
    )
)
```

## Multi-Project Analysis

Analyze multiple dbt projects:

```python
dbt_projects = [
    {"path": "./analytics", "name": "Analytics"},
    {"path": "./marketing", "name": "Marketing"},
    {"path": "./finance", "name": "Finance"},
]

result = (
    CheckHub()
    .with_metrics([
        ModelCountMetric,
        ModelTestCoverageMetric,
        ModelDocumentationMetric,
    ])
    .with_providers([
        [DbtProvider(project_path=proj["path"])]
        for proj in dbt_projects
    ])
    .measure()
)
```

## Configuration

You can configure metric thresholds via YAML:

```yaml
# checkup.yaml
metrics:
  dbt_test_coverage:
    min_threshold: 80  # Alert if below 80%
  dbt_doc_coverage:
    min_threshold: 90  # Alert if below 90%
```

```python
result = (
    CheckHub(config_path=Path("checkup.yaml"))
    .with_metrics([ModelTestCoverageMetric, ModelDocumentationMetric])
    .with_providers([[DbtProvider(project_path="./analytics")]])
    .measure()
)
```
