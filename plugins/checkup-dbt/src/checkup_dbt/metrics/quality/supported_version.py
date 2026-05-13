import logging

from checkup.measurement import Measurement, Measurements
from checkup.metric import Metric
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.metrics.quality.version import DbtVersionMetric

logger = logging.getLogger(__name__)


class DbtSupportedVersionMetric(DbtMetric):
    """
    Metric for checking dbt version compatibility.
    """

    name: str = "dbt_supported_version"
    description: str = "Whether dbt version meets minimum requirement"
    unit: str = "boolean"

    min_version: str

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [DbtVersionMetric]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        version: str = measurements.get(DbtVersionMetric).value

        major_version = int(version.split(".")[0])
        minor_version = int(version.split(".")[1])
        min_major = int(self.min_version.split(".")[0])
        min_minor = int(self.min_version.split(".")[1])

        supported = major_version == min_major and minor_version >= min_minor

        value = 1 if supported else 0
        diagnostic = ""
        if not supported:
            diagnostic = (
                f"dbt version {version} does not meet minimum requirement of {self.min_version}. "
                f"Please upgrade dbt to version {self.min_version} or later."
            )
        logger.info(f"dbt version {version} supported: {bool(value)}")
        return self.measure(value=value, diagnostic=diagnostic)
