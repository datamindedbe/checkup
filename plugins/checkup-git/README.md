# checkup-git

Git repository metrics plugin for [checkup](https://pypi.org/project/checkup/).

## Installation

```bash
pip install checkup-git
```

## Requirements

- Python >= 3.12
- [checkup](https://pypi.org/project/checkup/)
- Git installed on the system

## Usage

```python
from checkup import CheckHub
from checkup_git import (
    GitProvider,
    GitDaysSinceLastUpdateMetric,
    GitTrackedFileCountMetric,
)

results = (
    CheckHub()
    .with_metrics([
        GitDaysSinceLastUpdateMetric(),
        GitTrackedFileCountMetric(),
    ])
    .with_providers([[
        GitProvider("./my_repo"),
    ]])
    .measure()
)
```

## Provider

### GitProvider

Extracts metadata from a git repository, including the last commit date and list of tracked files.

## Available Metrics

### GitDaysSinceLastUpdateMetric

Returns the number of days since the last git commit.

### GitTrackedFileCountMetric

Returns the number of git tracked files, optionally filtered by a glob pattern. Configure by subclassing:

```python
from checkup_git import GitTrackedFileCountMetric

class PythonTestFileCountMetric(GitTrackedFileCountMetric):
    name = "python_test_file_count"
    description = "Number of Python test files"
    pattern = "tests/test_*.py"
```

## Creating Custom Metrics

Extend `GitMetric` to create custom git-based metrics:

```python
from checkup_git import GitMetric

class MyCustomGitMetric(GitMetric):
    name = "my_custom_metric"
    description = "My custom git metric"

    def calculate(self, context, measurements):
        git_context = self.get_context(context)
        tracked_files = git_context.get("git_tracked_files", [])
        python_files = [f for f in tracked_files if f.endswith(".py")]
        return self.measure(value=len(python_files))
```
