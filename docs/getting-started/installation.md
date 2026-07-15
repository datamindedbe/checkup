# Installation

## Requirements

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

## Installing CheckUp

Add CheckUp to your project:

```bash
uv add checkup
```

To try CheckUp without adding it to a project, run the CLI directly:

```bash
uvx checkup
```

### From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/datamindedbe/checkup.git
cd checkup
uv sync
```

## Installing Plugins

Install plugins as needed:

### Git Plugin

For analyzing Git repositories:

```bash
uv add checkup-git
```

### dbt Plugin

For dbt project metrics:

```bash
uv add checkup-dbt
```

### Python Plugin

For Python project analysis:

```bash
uv add checkup-python
```

### Conveyor Plugin

For Conveyor platform integration:

```bash
uv add checkup-conveyor
```

## Verifying Installation

Verify the installation:

```bash
uv run checkup --version
```

This prints the installed version. To list the plugins available in your environment:

```bash
uv run checkup plugins
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
git clone https://github.com/datamindedbe/checkup.git
cd checkup

# Install with development dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=checkup
```
