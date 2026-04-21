import logging
from typing import ClassVar

from checkup.metric import Measurement, Metric
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.metrics.quality.version import DbtVersionMetric

logger = logging.getLogger(__name__)


class DbtSupportedVersionMetric(DbtMetric):
    """
    Metric for checking dbt version compatibility.
    """

    name: ClassVar[str] = "dbt_supported_version"
    description: ClassVar[str] = "Whether dbt version meets minimum requirement"
    unit: ClassVar[str] = "boolean"

    min_version: str

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [DbtVersionMetric]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        version: str = measurements[DbtVersionMetric].value

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
        return self.measurement(value=value, diagnostic=diagnostic)
