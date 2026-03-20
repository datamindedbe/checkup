# checkup-airflow

Airflow metrics plugin for [checkup](https://pypi.org/project/checkup/).

## Installation

```bash
pip install checkup-airflow
```

## Requirements

- Python >= 3.12
- [checkup](https://pypi.org/project/checkup/)

## Usage

```python
from checkup import CheckHub
from checkup_airflow import AirflowProvider

results = (
    CheckHub()
    .with_metrics([])
    .with_providers([
        AirflowProvider(),
    ])
    .measure()
)
```

## Provider

### AirflowProvider

Extracts metadata from an Airflow environment.
