import logging
from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.provider import DbtManifestProvider

logger = logging.getLogger(__name__)


class DbtColumnTestsMetric(DbtMetric):
    name: ClassVar[str] = "dbt_column_tests"
    description: ClassVar[str] = "Number of tests targeting specific columns"
    unit: ClassVar[str] = "tests"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context[DbtManifestProvider.name]["manifest"]
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
