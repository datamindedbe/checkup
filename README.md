<p align="center">
  <img src="https://raw.githubusercontent.com/datamindedbe/checkup/main/assets/banner.png" alt="CheckUp" width="100%" />
</p>

<h3 align="center">Computational Governance Framework</h3>
<p align="center">for measuring <b>data product health</b></p>

<p align="center">
  <a href="https://pypi.org/project/checkup/"><img src="https://img.shields.io/pypi/v/checkup" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/checkup/"><img src="https://img.shields.io/pypi/pyversions/checkup" alt="Python versions" /></a>
</p>

<p align="center">
  <!-- <img src="https://raw.githubusercontent.com/datamindedbe/checkup/main/images/demo.gif" alt="CheckUp demo" width="100%" /> -->
  <img src="./images/demo.gif" alt="CheckUp demo" width="100%" />
</p>

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
