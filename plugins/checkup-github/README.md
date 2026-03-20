# checkup-github

GitHub metrics plugin for [checkup](https://pypi.org/project/checkup/).

## Installation

```bash
pip install checkup-github
```

## Requirements

- Python >= 3.12
- [checkup](https://pypi.org/project/checkup/)

## Usage

```python
from checkup import CheckHub
from checkup_github import GitHubProvider

results = (
    CheckHub()
    .with_metrics([])
    .with_providers([
        GitHubProvider(),
    ])
    .measure()
)
```

## Provider

### GitHubProvider

Extracts metadata from a GitHub environment.
