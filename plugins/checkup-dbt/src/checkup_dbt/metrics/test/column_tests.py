import logging

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtColumnTestsMetric(DbtMetric):
    name: str = "dbt_column_tests"
    description: str = "Number of tests targeting specific columns"
    unit: str = "tests"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context["dbt_manifest"]
        self.value = len(
            [
                node
                for node in manifest.nodes.values()
                if node.resource_type == NodeType.Test
                and hasattr(node, "column_name")
                and node.column_name is not None
            ]
        )
        logger.info(f"Found {self.value} column tests")
