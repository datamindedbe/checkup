import logging

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


def is_output_model(node) -> bool:
    return node.resource_type == NodeType.Model and not node.schema.endswith("__int")


class DbtOutputModelsMetric(DbtMetric):
    name: str = "dbt_output_models"
    description: str = "Number of output models (non-internal schema)"
    unit: str = "models"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context["dbt_manifest"]
        self.value = len(
            [node for node in manifest.nodes.values() if is_output_model(node)]
        )
        logger.info(f"Found {self.value} output models")
