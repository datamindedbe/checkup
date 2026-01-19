import logging
from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtTestedColumnsMetric(DbtMetric):
    """Count columns that have at least one test.

    This metric uses set intersection logic that doesn't fit the standard
    count patterns, so it implements calculate() directly.
    """

    name: ClassVar[str] = "dbt_tested_columns"
    description: ClassVar[str] = "Number of columns with at least one test"
    unit: ClassVar[str] = "columns"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = self.get_manifest(context)

        all_columns = set(
            (node.unique_id, column_name)
            for node in manifest.nodes.values()
            if node.resource_type == NodeType.Model
            for column_name in node.columns.keys()
        )

        tested_columns = set(
            (node.attached_node, node.column_name)
            for node in manifest.nodes.values()
            if node.resource_type == NodeType.Test
            and hasattr(node, "attached_node")
            and hasattr(node, "column_name")
            and node.attached_node is not None
            and node.column_name is not None
        )

        self.value = len(all_columns & tested_columns)
        logger.info(f"Found {self.value} tested columns")
