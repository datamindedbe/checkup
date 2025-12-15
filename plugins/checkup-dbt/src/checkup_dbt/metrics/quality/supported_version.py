import logging

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtSupportedVersionMetric(DbtMetric):
    name: str = "dbt_supported_version"
    description: str = "Whether dbt version meets minimum requirement"
    unit: str = "boolean"

    expected_version: str = "1.9"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context["dbt_manifest"]
        version = manifest.metadata.dbt_version

        major_version = int(version.split(".")[0])
        minor_version = int(version.split(".")[1])
        expected_major = int(self.expected_version.split(".")[0])
        expected_minor = int(self.expected_version.split(".")[1])

        supported = major_version == expected_major and minor_version >= expected_minor

        self.value = 1 if supported else 0
        logger.info(f"dbt version {version} supported: {bool(self.value)}")
