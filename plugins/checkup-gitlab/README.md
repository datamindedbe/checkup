# checkup-gitlab

GitLab metrics plugin for [checkup](https://pypi.org/project/checkup/).

## Installation

```bash
pip install checkup-gitlab
```

## Requirements

- Python >= 3.12
- [checkup](https://pypi.org/project/checkup/)

## Usage

```python
from checkup import CheckHub
from checkup_gitlab import GitLabProvider

results = (
    CheckHub()
    .with_metrics([])
    .with_providers([
        GitLabProvider(),
    ])
    .measure()
)
```

## Provider

### GitLabProvider

Extracts metadata from a GitLab environment.
