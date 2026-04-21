from checkup_python.metrics.version_check import PythonVersionCheckMetric

from checkup.hub import CheckHub


def test_measure() -> None:
    result = (
        CheckHub()
        .with_metrics([PythonVersionCheckMetric(min_version="3.8", max_version="3.13")])
        .measure()
    )

    # `PythonVersionCheckMetric` depends on `PythonVersionMetric`
    assert len(result.measurements) == 2
