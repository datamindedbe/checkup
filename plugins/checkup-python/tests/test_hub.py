from pathlib import Path

from checkup_python.metrics.version_check import PythonVersionCheckMetric

from checkup.hub import CheckHub


def test_measure() -> None:
    config_path = Path(__file__).parent / "fixtures" / "test_config.yaml"

    result = (
        CheckHub(config_path=config_path)
        .with_metrics([PythonVersionCheckMetric])
        .measure()
    )

    # `PythonVersionCheckMetric` depends on `PythonVersionMetric`
    assert len(result.metrics) == 2
