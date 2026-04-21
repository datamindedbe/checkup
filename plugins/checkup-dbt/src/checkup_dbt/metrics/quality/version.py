"""Dbt version metric."""

import logging
from typing import ClassVar

from checkup.metric import Measurement, Metric
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtVersionMetric(DbtMetric):
    """
    Metric to detect the dbt version used to generate the manifest.
    """

    name: ClassVar[str] = "dbt_version"
    description: ClassVar[str] = "The dbt version used to generate the manifest"
    unit: ClassVar[str] = "version"

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        manifest = self.get_manifest(context)
        value = manifest.metadata.dbt_version
        return self.measure(value=value, diagnostic=f"dbt version: {value}")
