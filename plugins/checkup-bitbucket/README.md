# checkup-bitbucket

Bitbucket metrics plugin for [checkup](https://pypi.org/project/checkup/).

## Installation

```bash
pip install checkup-bitbucket
```

## Requirements

- Python >= 3.12
- [checkup](https://pypi.org/project/checkup/)

## Usage

```python
from checkup import CheckHub
from checkup_bitbucket import BitbucketProvider

results = (
    CheckHub()
    .with_metrics([])
    .with_providers([
        BitbucketProvider(),
    ])
    .measure()
)
```

## Provider

### BitbucketProvider

Extracts metadata from a Bitbucket environment.
