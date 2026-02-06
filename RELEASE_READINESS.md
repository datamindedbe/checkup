# Release Readiness Review — CheckUp v0.1.0

## Executive Summary

CheckUp is a well-engineered Python framework with strong code quality, good test
coverage on the core, and comprehensive documentation infrastructure. However, several
gaps must be addressed before a public release. The items below are organized by
priority.

---

## Blockers (Must Fix Before Release)

### 1. Missing LICENSE file

There is no LICENSE file in the repository. This is a hard blocker for any open-source
release — without it, the code is technically "all rights reserved" and nobody can
legally use, modify, or distribute it. Since this is an Apache Software Foundation
incubator project, an Apache 2.0 license is the expected choice.

### 2. Placeholder project description in `pyproject.toml:4`

```toml
description = "Add your description here"
```

This placeholder ships into PyPI metadata. It should be replaced with a real
description, e.g.:

```
"Extensible framework for measuring data product health through computational governance"
```

### 3. CLI entry point is a stub (`src/checkup/__init__.py:45-48`)

The `checkup` CLI command currently just prints two lines and exits:

```python
def main() -> None:
    print("Checkup metrics framework")
    print("Import CheckHub to get started")
```

Either implement a real CLI (e.g., using `click` or `argparse` to load a config and
run metrics) or remove the `[project.scripts]` entry from `pyproject.toml` to avoid
shipping a non-functional command.

### 4. `checkup-python` plugin is unimplemented (`plugins/checkup-python/src/checkup_python/__init__.py`)

The file contains only comments — no classes, no exports. This plugin should either be
implemented or removed from the workspace before release.

### 5. `checkup-git` plugin is a skeleton (`plugins/checkup-git/src/checkup_git/__init__.py`)

Contains a single empty `GitMetric(Metric)` class with `pass` and has zero tests.
Same recommendation: implement or remove.

### 6. Low test coverage on `executor.py` (17%)

The executor module — responsible for running metrics across THREAD, PROCESS, and
ASYNCIO backends — has only 17% line coverage. This is the most operationally critical
module in the framework. Key untested paths include:

- `ProcessPoolExecutor` metric execution (lines 131–199)
- `AsyncIOExecutor` execution (lines 217–235)
- Error handling during parallel execution (lines 284–305, 329–361)
- Metric pickling validation (lines 405–434)

### 7. Plugin tests fail in CI configuration

Running `uv run pytest tests/ plugins/*/tests plugins/*/test` (the exact CI command)
fails with `ModuleNotFoundError: No module named 'checkup_dbt'` unless
`--all-packages` is used with `uv sync`. The CI workflow does use `--all-packages`,
but local developer experience is broken without explicit documentation of this.

---

## Should Fix (Important for Quality)

### 8. No CHANGELOG

A CHANGELOG.md (or equivalent) is expected for any versioned release. Consider using
[Keep a Changelog](https://keepachangelog.com/) format. This also helps downstream
users understand what changed between versions.

### 9. No CONTRIBUTING guide

For an incubator project expecting community contributions, a CONTRIBUTING.md covering
development setup, testing instructions, plugin development, and PR expectations is
important.

### 10. README is too sparse

The current README is 11 lines with no installation instructions, no usage example, no
badges, and no link to the full documentation. The README is the first thing potential
users see. Consider including:

- Project description and motivation
- Installation instructions (`pip install checkup`)
- Minimal usage example
- Link to full docs
- CI/coverage/license badges
- Contributing link

### 11. Coverage reporting only covers core, not plugins

The CI `--cov=src/checkup` flag only measures core coverage. Plugin code
(`plugins/*/src/`) is not measured. Add `--cov` flags for each plugin to get a
complete picture.

### 12. No `py.typed` marker

For downstream consumers using type checkers, a `py.typed` marker file in the package
signals that the library ships type information. Since the codebase uses thorough type
annotations, adding `src/checkup/py.typed` (empty file) would unlock this value.

### 13. Test warning: `test_html_materializer_end_to_end` returns a value

Pytest flags this with `PytestReturnNotNoneWarning`. The test function returns a
`PosixPath` instead of using an assertion. This should be a simple fix.

### 14. Missing `project.urls` in `pyproject.toml`

Package metadata should include links for users to find docs, source, and issue
tracker:

```toml
[project.urls]
Homepage = "https://github.com/datamindedbe/incubator-checkup"
Documentation = "https://datamindedbe.github.io/incubator-checkup/"
Repository = "https://github.com/datamindedbe/incubator-checkup"
Issues = "https://github.com/datamindedbe/incubator-checkup/issues"
```

### 15. No release/publish CI workflow

There is no GitHub Actions workflow for publishing to PyPI. Consider adding a workflow
triggered on tag push (e.g., `v*`) that builds and publishes using `uv build` and
`twine upload` or the `pypa/gh-action-pypi-publish` action.

---

## Nice to Have (Suggestions for Improvement)

### 16. Multi-Python version testing

CI only tests against Python 3.12. Since `requires-python = ">=3.12"`, testing 3.12
and 3.13 via a matrix build would validate forward compatibility.

### 17. `errors.py` has 41% coverage

While error paths are harder to test, the custom exceptions (`ProviderError`,
`MetricPicklingError`, `DuplicateMetricNameError`) should have explicit unit tests
verifying their messages and attributes.

### 18. Add `[tool.pytest.ini_options]` to `pyproject.toml`

Centralizing pytest configuration (test paths, markers, default flags) avoids
developers needing to remember the long `pytest tests/ plugins/*/tests ...` invocation.

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "plugins/checkup-dbt/tests", "plugins/checkup-conveyor/tests"]
addopts = "--cov=src/checkup --cov-report=term-missing -q"
```

### 19. Consider classifiers in `pyproject.toml`

PyPI classifiers help users discover the package:

```toml
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Topic :: Software Engineering :: Quality Assurance",
    "Programming Language :: Python :: 3.12",
]
```

### 20. Pin or cap major dependency versions

Current lower bounds are good (`pydantic>=2.11.7`), but no upper bounds exist. For a
framework consumed as a library, consider capping major versions
(`pydantic>=2.11.7,<3`) to prevent breaking changes from propagating silently.

### 21. Add a security policy (SECURITY.md)

A SECURITY.md with instructions for responsibly disclosing vulnerabilities is a best
practice for any open-source project.

---

## Current Scorecard

| Area                    | Status | Details                                    |
|-------------------------|--------|--------------------------------------------|
| License                 | **Missing** | No LICENSE file                         |
| Package metadata        | **Incomplete** | Placeholder description, no URLs, no classifiers |
| Core code quality       | Good   | Clean patterns, type hints, logging        |
| Core test coverage      | 66%    | Good on graph/materializers, weak on executor |
| Plugin maturity         | Mixed  | dbt: solid, conveyor: ok, git/python: stubs |
| Documentation site      | Good   | MkDocs + Material, comprehensive content   |
| README                  | Sparse | 11 lines, no install/usage instructions    |
| CI/CD                   | Partial | Lint + test present, no release pipeline  |
| CLI                     | Stub   | Entry point does nothing useful            |
| Changelog               | **Missing** | No CHANGELOG.md                        |
| Contributing guide      | **Missing** | No CONTRIBUTING.md                     |
| Security policy         | **Missing** | No SECURITY.md                         |
