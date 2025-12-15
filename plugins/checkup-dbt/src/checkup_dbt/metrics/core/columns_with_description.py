import logging

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtColumnsWithDescriptionMetric(DbtMetric):
    name: str = "dbt_columns_with_description"
    description: str = "Number of columns with descriptions"
    unit: str = "columns"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context["dbt_manifest"]
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
