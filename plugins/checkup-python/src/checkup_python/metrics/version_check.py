from checkup.measurement import Measurement, Measurements
from checkup.metric import Metric
from checkup.types import Context
from checkup_python.metrics.utils import parse_semantic_version
from checkup_python.metrics.version import PythonVersionMetric


class PythonVersionCheckMetric(Metric):
    """
    Metric that checks the Python version of the current project
    and compares it to given thresholds.
    """

    name: str = "python_version_check"
    description: str = "The Python version adheres to a minimum and maximum boundary"
    unit: str = "bool"

    min_version: str
    max_version: str

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [PythonVersionMetric]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        actual_version = measurements.get(PythonVersionMetric).value

        actual = parse_semantic_version(actual_version)
        min_ver = parse_semantic_version(self.min_version)
        max_ver = parse_semantic_version(self.max_version)

        value = min_ver <= actual <= max_ver
        return self.measure(value=value)
