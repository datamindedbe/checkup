# checkup-python

Python project metrics plugin for [checkup](https://pypi.org/project/checkup/).

## Installation

```bash
pip install checkup-python
```

## Requirements

- Python >= 3.12
- [checkup](https://pypi.org/project/checkup/)

## Usage

```python
from checkup import CheckHub
from checkup_python.metrics import PythonVersionMetric

results = (
    CheckHub()
    .with_metrics([PythonVersionMetric])
    .measure()
)
```

## Available Metrics

### PythonVersionMetric

Detects the Python version configured for a project.

**Detection order:**
1. `.python-version` file
2. `pyproject.toml` (`requires-python` field)
3. Falls back to current runtime version

The metric supports comparison operators for version checking.

### PythonVersionCheckMetric

Checks if the project's Python version falls within specified minimum and maximum boundaries. Configure by subclassing:

```python
from checkup_python.metrics.version_check import PythonVersionCheckMetric

class MyVersionCheck(PythonVersionCheckMetric):
    min_version = "3.11"
    max_version = "3.13"
```
