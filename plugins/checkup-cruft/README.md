# checkup-cruft

Cruft template metrics plugin for [checkup](https://pypi.org/project/checkup/).

Tracks how well a project stays in sync with its [cruft](https://cruft.github.io/cruft/) (cookiecutter) template.

## Installation

```bash
pip install checkup-cruft
```

## Requirements

- Python >= 3.12
- [checkup](https://pypi.org/project/checkup/)
- Git installed on the system
- Network access to the template repository (only for the drift metrics below)

## Usage

```python
from checkup import CheckHub
from checkup_cruft import (
    CruftProvider,
    CruftLinkedMetric,
    CruftDaysSinceUpdateMetric,
    CruftConflictCountMetric,
    CruftUpToDateMetric,
)

results = (
    CheckHub()
    .with_metrics([
        CruftLinkedMetric(),
        CruftDaysSinceUpdateMetric(),
        CruftConflictCountMetric(),
        CruftUpToDateMetric(),
    ])
    .with_providers([[
        CruftProvider("./my_product", fetch_template=True),
    ]])
    .measure()
)
```

## Provider

### CruftProvider

Reads `.cruft.json` from the project (template URL, pinned commit, `.rej` conflict
markers, and the last commit that touched `.cruft.json`).

`fetch_template=True` additionally clones the template repository and compares the
pinned commit against the template head. Leave it off (the default) for a fully
local, offline run: the drift metrics then report `None`.

## Available Metrics

### Local (no network)

| Metric                       | Unit    | Description                                             |
| ---------------------------- | ------- | ------------------------------------------------------- |
| `CruftLinkedMetric`          | boolean | Whether a `.cruft.json` is present                      |
| `CruftDaysSinceUpdateMetric` | days    | Days since `.cruft.json` last changed in git            |
| `CruftConflictCountMetric`   | files   | Number of `*.rej` files left by a failed `cruft update` |

### Template drift (requires `fetch_template=True`)

| Metric                          | Unit    | Description                                             |
| ------------------------------- | ------- | ------------------------------------------------------- |
| `CruftUpToDateMetric`           | boolean | Whether the pinned commit matches the template head     |
| `CruftCommitsBehindMetric`      | commits | Template commits between the pinned commit and the head |
| `CruftDaysBehindTemplateMetric` | days    | Days between the pinned commit and the template head    |

## Creating Custom Metrics

Extend `CruftMetric` to read the cruft context directly:

```python
from checkup_cruft import CruftMetric

class TemplateUrlMetric(CruftMetric):
    name = "cruft_template_url"
    description = "Configured cruft template URL"

    def calculate(self, context, measurements):
        cruft = self.get_context(context)
        return self.measure(value=cruft.get("template"))
```
