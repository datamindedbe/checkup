# CheckUp

[![PyPI version](https://img.shields.io/pypi/v/checkup)](https://pypi.org/project/checkup/)
[![Python versions](https://img.shields.io/pypi/pyversions/checkup)](https://pypi.org/project/checkup/)

Computational governance framework for measuring data product health.

## Plugins

Checkup uses plugins to provide metrics for different tools and platforms.

| Plugin | Version | Status | Description |
|--------|---------|--------|-------------|
| [checkup-dbt](https://pypi.org/project/checkup-dbt/) | [![PyPI](https://img.shields.io/pypi/v/checkup-dbt)](https://pypi.org/project/checkup-dbt/) | Usable | dbt metrics |
| [checkup-git](https://pypi.org/project/checkup-git/) | [![PyPI](https://img.shields.io/pypi/v/checkup-git)](https://pypi.org/project/checkup-git/) | Usable | Git repository metrics |
| [checkup-python](https://pypi.org/project/checkup-python/) | [![PyPI](https://img.shields.io/pypi/v/checkup-python)](https://pypi.org/project/checkup-python/) | Early | Python project metrics |
| [checkup-conveyor](https://pypi.org/project/checkup-conveyor/) | [![PyPI](https://img.shields.io/pypi/v/checkup-conveyor)](https://pypi.org/project/checkup-conveyor/) | Early | [Conveyor](https://conveyor.dataminded.com/) API metrics |
| [checkup-airflow](https://pypi.org/project/checkup-airflow/) | [![PyPI](https://img.shields.io/pypi/v/checkup-airflow)](https://pypi.org/project/checkup-airflow/) | Planned | Airflow metrics |
| [checkup-bitbucket](https://pypi.org/project/checkup-bitbucket/) | [![PyPI](https://img.shields.io/pypi/v/checkup-bitbucket)](https://pypi.org/project/checkup-bitbucket/) | Planned | Bitbucket metrics |
| [checkup-github](https://pypi.org/project/checkup-github/) | [![PyPI](https://img.shields.io/pypi/v/checkup-github)](https://pypi.org/project/checkup-github/) | Planned | GitHub metrics |
| [checkup-gitlab](https://pypi.org/project/checkup-gitlab/) | [![PyPI](https://img.shields.io/pypi/v/checkup-gitlab)](https://pypi.org/project/checkup-gitlab/) | Planned | GitLab metrics |

## Key Concepts

- **Metrics** - Calculate values from context
- **Providers** - Functions that enrich context (shared across metrics)
- **Materializers** - Output formats (Console, HTML, CSV, etc.)
