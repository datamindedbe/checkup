# Installation

## Requirements

- Python 3.12 or higher
- pip or uv package manager

## Installing CheckUp

### Using pip

```bash
pip install checkup
```

### Using uv

```bash
uv add checkup
```

### From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/datamindedbe/incubator-checkup.git
cd incubator-checkup
uv sync
```

## Installing Plugins

CheckUp provides several plugins for specific use cases. Install them as needed:

### Git Plugin

For analyzing Git repositories:

```bash
pip install checkup-git
```

### dbt Plugin

For dbt project metrics:

```bash
pip install checkup-dbt
```

### Python Plugin

For Python project analysis:

```bash
pip install checkup-python
```

### Conveyor Plugin

For Conveyor platform integration:

```bash
pip install checkup-conveyor
```

## Verifying Installation

After installation, verify that CheckUp is correctly installed:

```bash
checkup
```

You should see:

```
Checkup metrics framework
Import CheckHub to get started
```

Or verify in Python:

```python
import checkup
print(checkup.__all__)
```

## Development Setup

For contributing to CheckUp:

```bash
# Clone the repository
git clone https://github.com/datamindedbe/incubator-checkup.git
cd incubator-checkup

# Install with development dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=checkup
```
