# checkup-conveyor

Conveyor metrics plugin for [checkup](https://pypi.org/project/checkup/).

## Installation

```bash
pip install checkup-conveyor
```

## Requirements

- Python >= 3.12
- [checkup](https://pypi.org/project/checkup/)
- requests

## Usage

```python
from checkup import CheckHub
from checkup_conveyor import ConveyorProvider

results = (
    CheckHub()
    .with_metrics([])
    .with_providers([[
        ConveyorProvider(
            project_name="my-project",
            api_key="your-api-key",
            environment_name="production",
        ),
    ]])
    .measure()
)
```

## Provider

### ConveyorProvider

Provides Conveyor API context for metrics, including project name, environment name, and an authenticated API client.

## Creating Custom Metrics

Extend `ConveyorMetric` to create custom Conveyor-based metrics:

```python
from checkup_conveyor import ConveyorMetric

class MyConveyorMetric(ConveyorMetric):
    name = "my_conveyor_metric"
    description = "My custom Conveyor metric"

    def calculate(self, context, measurements):
        api_client = self.get_api_client(context)
        project_name = self.get_project_name(context)
        environment_name = self.get_environment_name(context)

        # Use api_client to fetch data from Conveyor
        value = ...
        return self.measure(value=value)
```
