# Conveyor Plugin

The Conveyor plugin provides metrics for monitoring projects deployed on the Conveyor platform.

## Installation

```bash
pip install checkup-conveyor
```

**Note:** This plugin requires the `requests` library.

## Provider

### ConveyorProvider

Connects to the Conveyor API to fetch project and deployment information.

```python
from checkup_conveyor import ConveyorProvider

provider = ConveyorProvider(
    api_url="https://api.conveyor.example.com",
    api_token="your-api-token",
    project_id="project-123"
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_url` | `str` | Yes | Conveyor API base URL |
| `api_token` | `str` | Yes | API authentication token |
| `project_id` | `str` | Yes | Project identifier |

**Context Data:**

The provider adds the following data under the `conveyor` namespace:

```python
context["conveyor"] = {
    "project": {...},         # Project metadata
    "deployments": [...],     # List of deployments
    "environments": [...],    # Available environments
    "jobs": [...],            # Scheduled jobs
    "status": "...",          # Current project status
}
```

## Metrics

### DeploymentCountMetric

Counts total deployments.

```python
from checkup_conveyor import DeploymentCountMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `conveyor_deployment_count` |
| Unit | `deployments` |
| Dependencies | None |
| Providers | `ConveyorProvider` |

### DeploymentSuccessRateMetric

Calculates the deployment success rate.

```python
from checkup_conveyor import DeploymentSuccessRateMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `conveyor_success_rate` |
| Unit | `percent` |
| Dependencies | `DeploymentCountMetric` |
| Providers | `ConveyorProvider` |

### JobHealthMetric

Monitors scheduled job health.

```python
from checkup_conveyor import JobHealthMetric
```

| Attribute | Value |
|-----------|-------|
| Name | `conveyor_job_health` |
| Unit | `percent` |
| Dependencies | None |
| Providers | `ConveyorProvider` |

## Example Usage

```python
import os
from checkup import CheckHub, ConsoleMaterializer
from checkup_conveyor import (
    ConveyorProvider,
    DeploymentCountMetric,
    DeploymentSuccessRateMetric,
    JobHealthMetric,
)

# Get credentials from environment
api_token = os.environ["CONVEYOR_API_TOKEN"]

result = (
    CheckHub()
    .with_metrics([
        DeploymentCountMetric,
        DeploymentSuccessRateMetric,
        JobHealthMetric,
    ])
    .with_providers([
        [ConveyorProvider(
            api_url="https://api.conveyor.example.com",
            api_token=api_token,
            project_id="analytics-pipeline"
        )],
    ])
    .measure()
)

result.materialize(
    ConsoleMaterializer(group_tag_1="project", group_tag_2="environment")
)
```

## Multi-Project Monitoring

Monitor multiple Conveyor projects:

```python
projects = [
    {"id": "analytics-pipeline", "name": "Analytics"},
    {"id": "etl-jobs", "name": "ETL"},
    {"id": "ml-training", "name": "ML Training"},
]

result = (
    CheckHub()
    .with_metrics([
        DeploymentSuccessRateMetric,
        JobHealthMetric,
    ])
    .with_providers([
        [ConveyorProvider(
            api_url=api_url,
            api_token=api_token,
            project_id=proj["id"]
        )]
        for proj in projects
    ])
    .measure()
)
```

## Environment Variables

For security, use environment variables for sensitive configuration:

```bash
export CONVEYOR_API_URL="https://api.conveyor.example.com"
export CONVEYOR_API_TOKEN="your-secure-token"
```

```python
import os

provider = ConveyorProvider(
    api_url=os.environ["CONVEYOR_API_URL"],
    api_token=os.environ["CONVEYOR_API_TOKEN"],
    project_id="my-project"
)
```

## Error Handling

The provider handles API errors gracefully:

```python
context["conveyor"] = {
    "error": "Connection timeout",  # Set if API call fails
    "project": None,
    "deployments": [],
    # ...
}
```

Check for errors in your metrics:

```python
class SafeMetric(Metric):
    def calculate(self, context, measurements):
        conveyor = context.get("conveyor", {})
        if conveyor.get("error"):
            return self.measure(
                value=None,
                diagnostic=f"API Error: {conveyor['error']}"
            )
        # Normal calculation...
        return self.measure(value=computed_value)
```
