from checkup_python.metrics import PythonVersionMetric


def test_python_version_metric_calculate() -> None:
    metric = PythonVersionMetric()
    measurement = metric.calculate(context={}, measurements={})

    assert measurement.value is not None
