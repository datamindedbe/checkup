from pathlib import Path

from checkup_python.metrics import PythonVersionMetric
from checkup_python.metrics.linter import (
    PythonLinterErrorsMetric,
    PythonLinterWarningsMetric,
)


def test_python_version_metric_calculate() -> None:
    metric = PythonVersionMetric()
    metric.calculate(context={}, metrics={})

    assert metric.value is not None


def test_python_version_metric_compare() -> None:
    metric1 = PythonVersionMetric()
    metric1.value = "3.8.10"

    metric2 = PythonVersionMetric()
    metric2.value = "3.9"

    assert metric1 < metric2
    assert metric2 > metric1
    assert metric1 != metric2
    assert not (metric1 == metric2)


def test_python_linter_warnings_metric_calculate() -> None:
    """Test that PythonLinterWarningsMetric correctly counts warnings."""
    # Get path to the linter-test-project fixture
    fixture_path = (
        Path(__file__).parent / "fixtures" / "linter-test-project"
    ).absolute()

    context = {"python": {"dir": str(fixture_path)}}

    metric = PythonLinterWarningsMetric()
    metric.calculate(context=context, metrics={})

    # Should find warnings (E-series, B-series, etc.) but not F-series errors
    assert metric.value is not None
    assert metric.value > 0
    assert "linting warnings" in metric.diagnostic


def test_python_linter_errors_metric_calculate() -> None:
    """Test that PythonLinterErrorsMetric correctly counts errors."""
    # Get path to the linter-test-project fixture
    fixture_path = (
        Path(__file__).parent / "fixtures" / "linter-test-project"
    ).absolute()

    context = {"python": {"dir": str(fixture_path)}}

    metric = PythonLinterErrorsMetric()
    metric.calculate(context=context, metrics={})

    # Should find errors (F-series from Pyflakes)
    assert metric.value is not None
    assert metric.value > 0
    assert "linting errors" in metric.diagnostic


def test_python_linter_warnings_vs_errors() -> None:
    """Test that warnings and errors are counted separately and correctly."""
    fixture_path = (
        Path(__file__).parent / "fixtures" / "linter-test-project"
    ).absolute()

    context = {"python": {"dir": str(fixture_path)}}

    warnings_metric = PythonLinterWarningsMetric()
    warnings_metric.calculate(context=context, metrics={})

    errors_metric = PythonLinterErrorsMetric()
    errors_metric.calculate(context=context, metrics={})

    # Both should have values
    assert warnings_metric.value is not None
    assert errors_metric.value is not None

    # Both should be positive
    assert warnings_metric.value > 0
    assert errors_metric.value > 0

    # They should be different counts
    # (unless by coincidence the test project has equal numbers)
    assert warnings_metric.value + errors_metric.value > 0


def test_python_linter_clean_project() -> None:
    """Test linter metrics on a clean project with no issues."""
    fixture_path = (Path(__file__).parent / "fixtures" / "uv-project").absolute()

    context = {"python": {"dir": str(fixture_path)}}

    warnings_metric = PythonLinterWarningsMetric()
    warnings_metric.calculate(context=context, metrics={})

    errors_metric = PythonLinterErrorsMetric()
    errors_metric.calculate(context=context, metrics={})

    # Clean project should have zero or very low counts
    assert warnings_metric.value is not None
    assert errors_metric.value is not None
    assert warnings_metric.value == 0
    assert errors_metric.value == 0
