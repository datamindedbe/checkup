import logging

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtColumnsMetric(DbtMetric):
    name: str = "dbt_columns"
    description: str = "Total number of columns across all models"
    unit: str = "columns"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context["dbt_manifest"]
        self.value = len(
            [
                (node.name, column_name)
                for node in manifest.nodes.values()
                if node.resource_type == NodeType.Model
                for column_name in node.columns.keys()
            ]
        )
        logger.info(f"Found {self.value} columns")
