"""Dbt version metric."""

import logging
from typing import ClassVar

from checkup.metric import Metric
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtVersionMetric(DbtMetric):
    """Metric to detect the dbt version used to generate the manifest."""

    name: ClassVar[str] = "dbt_version"
    description: ClassVar[str] = "The dbt version used to generate the manifest"
    unit: ClassVar[str] = "version"

    def calculate(self, context: Context, metrics: dict[type[Metric], Metric]) -> None:
        manifest = self.get_manifest(context)
        self.value = manifest.metadata.dbt_version
        self.diagnostic = f"dbt version: {self.value}"
        logger.info(f"dbt version: {self.value}")
