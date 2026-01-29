from checkup_python.metrics import PythonVersionMetric


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
