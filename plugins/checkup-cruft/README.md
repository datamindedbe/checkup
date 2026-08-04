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
- Network access to the template repository (only for the drift metrics)

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
        CruftProvider(project_path="./my_product", fetch_template=True),
    ]])
    .measure()
)
```

## Provider

### CruftProvider

Reads `.cruft.json` from the project (template URL, pinned commit, and the `.rej`
conflict markers left by a failed `cruft update`). With `fetch_template=True` it
also clones the template repository to compare the pinned commit against the
template head; leave it off (the default) for a fully local, offline run, in which
case the drift metrics report `None`.

## Available Metrics

### Local Metrics

#### CruftLinkedMetric

Whether a `.cruft.json` template link is present.

#### CruftDaysSinceUpdateMetric

Days since `.cruft.json` last changed in git.

#### CruftConflictCountMetric

Number of `*.rej` files left by a failed `cruft update`.

### Template Drift Metrics

These require the provider to run with `fetch_template=True`.

#### CruftUpToDateMetric

Whether the pinned commit matches the latest template commit.

#### CruftCommitsBehindMetric

Number of template commits between the pinned commit and the head.

#### CruftDaysBehindTemplateMetric

Days between the pinned commit and the template head.

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
