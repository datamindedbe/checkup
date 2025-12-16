import logging
from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.provider import DbtManifestProvider

logger = logging.getLogger(__name__)


class DbtColumnsWithDescriptionMetric(DbtMetric):
    name: ClassVar[str] = "dbt_columns_with_description"
    description: ClassVar[str] = "Number of columns with descriptions"
    unit: ClassVar[str] = "columns"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context[DbtManifestProvider.name]["manifest"]
        self.value = len(
            [
                (node.name, column_name)
                for node in manifest.nodes.values()
                if node.resource_type == NodeType.Model
                for column_name, column in node.columns.items()
                if column.description != ""
            ]
        )
        logger.info(f"Found {self.value} columns with descriptions")
