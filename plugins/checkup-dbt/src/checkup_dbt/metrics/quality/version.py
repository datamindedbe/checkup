"""Dbt version metric."""

import logging

from checkup.metric import Measurement, Metric
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtVersionMetric(DbtMetric):
    """
    Metric to detect the dbt version used to generate the manifest.
    """

    name: str = "dbt_version"
    description: str = "The dbt version used to generate the manifest"
    unit: str = "version"

    def calculate(
        self, context: Context, measurements: dict[type[Metric], list[Measurement]]
    ) -> Measurement:
        manifest = self.get_manifest(context)
        value = manifest.metadata.dbt_version
        return self.measure(value=value, diagnostic=f"dbt version: {value}")
