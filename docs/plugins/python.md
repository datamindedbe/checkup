# Python Plugin

The Python plugin provides metrics for analyzing Python projects.

## Installation

```bash
pip install checkup-python
```

## Provider

### PythonProjectProvider

Analyzes Python project structure and metadata.

```python
from checkup_python import PythonProjectProvider

provider = PythonProjectProvider(project_path="/path/to/project")
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_path` | `str` or `Path` | Yes | Path to the Python project |

**Context Data:**

The provider adds the following data under the `python` namespace:

```python
context["python"] = {
    "source_files": [...],    # List of .py files
    "test_files": [...],      # List of test files
    "packages": [...],        # List of packages
    "pyproject": {...},       # Parsed pyproject.toml
    "requirements": [...],    # List of dependencies
    "total_lines": 0,         # Total lines of Python code
}
```

## Metrics

### FileCountMetric

Counts Python source files.

```python
from checkup_python import FileCountMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `python_file_count` |
| Unit | `files` |
| Dependencies | None |
| Providers | `PythonProjectProvider` |

### LineCountMetric

Counts total lines of Python code.

```python
from checkup_python import LineCountMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `python_line_count` |
| Unit | `lines` |
| Dependencies | None |
| Providers | `PythonProjectProvider` |

### TestFileRatioMetric

Calculates the ratio of test files to source files.

```python
from checkup_python import TestFileRatioMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `python_test_ratio` |
| Unit | `ratio` |
| Dependencies | `FileCountMetric` |
| Providers | `PythonProjectProvider` |

### DependencyCountMetric

Counts project dependencies.

```python
from checkup_python import DependencyCountMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `python_dependency_count` |
| Unit | `dependencies` |
| Dependencies | None |
| Providers | `PythonProjectProvider` |

## Example Usage

```python
from checkup import CheckHub, ConsoleMaterializer
from checkup_python import (
    PythonProjectProvider,
    FileCountMetric,
    LineCountMetric,
    TestFileRatioMetric,
    DependencyCountMetric,
)

result = (
    CheckHub()
    .with_metrics([
        FileCountMetric,
        LineCountMetric,
        TestFileRatioMetric,
        DependencyCountMetric,
    ])
    .with_providers([
        [PythonProjectProvider(project_path="./my-package")],
    ])
    .measure()
)

result.materialize(
    ConsoleMaterializer(group_tag_1="project", group_tag_2="type")
)
```

## Multi-Package Analysis

Analyze a monorepo with multiple Python packages:

```python
from pathlib import Path

packages = list(Path("./packages").glob("*/pyproject.toml"))

result = (
    CheckHub()
    .with_metrics([
        FileCountMetric,
        LineCountMetric,
        DependencyCountMetric,
    ])
    .with_providers([
        [PythonProjectProvider(project_path=pkg.parent)]
        for pkg in packages
    ])
    .measure()
)
```

## Workspace Analysis

For UV/Poetry workspaces:

```python
from checkup import CheckHub
from checkup_python import PythonProjectProvider, FileCountMetric

# Analyze root and all workspace members
workspace_members = [
    ".",
    "./plugins/checkup-git",
    "./plugins/checkup-dbt",
    "./plugins/checkup-python",
]

result = (
    CheckHub()
    .with_metrics([FileCountMetric])
    .with_providers([
        [PythonProjectProvider(project_path=member)]
        for member in workspace_members
    ])
    .measure()
)
```
