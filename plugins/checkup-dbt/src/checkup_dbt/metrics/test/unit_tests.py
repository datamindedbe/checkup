import logging
from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.provider import DbtManifestProvider

logger = logging.getLogger(__name__)


class DbtUnitTestsMetric(DbtMetric):
    name: ClassVar[str] = "dbt_unit_tests"
    description: ClassVar[str] = "Number of singular (unit) tests"
    unit: ClassVar[str] = "tests"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context[DbtManifestProvider.name]["manifest"]
        self.value = len(
            [
                node
                for node in manifest.nodes.values()
                if node.resource_type == NodeType.Test
                and getattr(node, "test_node_type", None) == "singular"
            ]
        )
        logger.info(f"Found {self.value} unit tests")
