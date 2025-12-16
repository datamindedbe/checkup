import logging
from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.provider import DbtManifestProvider

logger = logging.getLogger(__name__)


class DbtColumnsMetric(DbtMetric):
    name: ClassVar[str] = "dbt_columns"
    description: ClassVar[str] = "Total number of columns across all models"
    unit: ClassVar[str] = "columns"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context[DbtManifestProvider.name]["manifest"]
        self.value = len(
            [
                (node.name, column_name)
                for node in manifest.nodes.values()
                if node.resource_type == NodeType.Model
                for column_name in node.columns.keys()
            ]
        )
        logger.info(f"Found {self.value} columns")
