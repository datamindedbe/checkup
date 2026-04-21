# Materializers

Materializers format and output calculated metrics. They transform raw metric data into human-readable or machine-processable formats.

## Available Materializers

CheckUp includes three built-in materializers:

| Materializer | Output | Use Case |
|-------------|--------|----------|
| `ConsoleMaterializer` | Terminal tables | Interactive viewing |
| `CSVMaterializer` | CSV file | Data analysis, spreadsheets |
| `HTMLMaterializer` | HTML report | Sharing, dashboards |

## Using Materializers

Materializers are called on `MeasurementResult`:

```python
from checkup import CheckHub, ConsoleMaterializer

result = CheckHub().with_metrics([MyMetric()]).measure()
result.materialize(ConsoleMaterializer(group_tag_1="domain", group_tag_2="project"))
```

## Console Materializer

Outputs metrics as rich tables in the terminal:

```python
from checkup import ConsoleMaterializer

result.materialize(
    ConsoleMaterializer(
        group_tag_1="domain",      # First grouping level
        group_tag_2="project",     # Second grouping level
        include_indirect=False     # Only show directly requested metrics
    )
)
```

Output example:

```
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Name        ┃ Description           ┃ Value ┃ Unit   ┃ Diagnostics   ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ file_count  │ Number of files       │    42 │ files  │ Found 42      │
│ line_count  │ Total lines of code   │  1234 │ lines  │               │
└─────────────┴───────────────────────┴───────┴────────┴───────────────┘
```

## CSV Materializer

Exports metrics to a CSV file for further analysis:

```python
from checkup import CSVMaterializer
from pathlib import Path

result.materialize(
    CSVMaterializer(
        output_path=Path("metrics.csv"),
        include_indirect=False
    )
)
```

Output format:

```csv
name,value,unit,diagnostic,description
file_count,42,files,Found 42,Number of files
line_count,1234,lines,,Total lines of code
```

## HTML Materializer

Generates a styled HTML report with hierarchical grouping:

```python
from checkup import HTMLMaterializer
from pathlib import Path

result.materialize(
    HTMLMaterializer(
        output_path=Path("report.html"),
        group_tag_1="domain",
        group_tag_2="project",
        include_indirect=True
    )
)
```

Features:

- Bootstrap-styled layout
- Collapsible accordion groups
- Responsive design
- Color-coded values

## Multiple Outputs

You can materialize to multiple formats:

```python
result = CheckHub().with_metrics([MyMetric()]).measure()

# Output to console
result.materialize(ConsoleMaterializer(group_tag_1="domain", group_tag_2="project"))

# Also save to CSV
result.materialize(CSVMaterializer(output_path=Path("metrics.csv")))

# And generate HTML report
result.materialize(
    HTMLMaterializer(
        output_path=Path("report.html"),
        group_tag_1="domain",
        group_tag_2="project"
    )
)
```

## Filtering Metrics

The `include_indirect` parameter controls which metrics are shown:

```python
# Only show metrics you explicitly requested
result.materialize(
    ConsoleMaterializer(
        group_tag_1="domain",
        group_tag_2="project",
        include_indirect=False  # Default
    )
)

# Show all metrics, including dependencies
result.materialize(
    ConsoleMaterializer(
        group_tag_1="domain",
        group_tag_2="project",
        include_indirect=True
    )
)
```

## Grouping by Tags

Materializers group output by metric tags:

```python
class MyMetric(Metric):
    def calculate(self, context, measurements):
        return self.measure(
            value=42,
            tags={"domain": "analytics", "project": "dashboard"}
        )
```

When materialized with `group_tag_1="domain"` and `group_tag_2="project"`, metrics are grouped accordingly.

## Creating Custom Materializers

Create custom materializers by extending the base class:

```python
from checkup import Materializer, Measurement
from pathlib import Path


class JSONMaterializer(Materializer):
    """Output metrics as JSON."""

    output_path: Path

    def materialize(self, measurements: list[Measurement], direct_metric_names: set[str]) -> None:
        filtered = self._filter_measurements(measurements, direct_metric_names)

        data = [
            {
                "name": m.metric.name,
                "value": m.value,
                "unit": m.metric.unit,
                "description": m.metric.description,
                "diagnostic": m.diagnostic,
                "tags": m.tags,
            }
            for m in filtered
        ]

        import json
        with open(self.output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
```

## Utility Functions

CheckUp provides helper functions for grouping measurements:

```python
from checkup.materializers import group_measurements_by_tags, group_measurements_hierarchical

# Flat grouping by two tags
groups = group_measurements_by_tags(
    measurements,
    tag1="domain",
    tag2="project",
    default_value="Unknown"
)
# Returns: {("analytics", "dashboard"): [measurements...]}

# Hierarchical grouping
hierarchy = group_measurements_hierarchical(
    measurements,
    tag1="domain",
    tag2="project",
    default_value="Ungrouped"
)
# Returns: {"analytics": {"dashboard": [measurements...]}}
```

## Best Practices

1. **Choose the right format**: Console for debugging, CSV for analysis, HTML for sharing
2. **Use meaningful tags**: Good tag names make grouped output more useful
3. **Consider your audience**: Technical users may prefer CSV, stakeholders may prefer HTML
4. **Materialize to multiple formats**: It's cheap to output to several formats at once
5. **Use `include_indirect` wisely**: Usually you want only directly requested metrics
