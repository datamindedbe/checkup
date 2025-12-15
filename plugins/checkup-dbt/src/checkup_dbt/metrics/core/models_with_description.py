import logging

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtModelsWithDescriptionMetric(DbtMetric):
    name: str = "dbt_models_with_description"
    description: str = "Number of models with descriptions"
    unit: str = "models"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context["dbt_manifest"]
        self.value = len(
            [
                node
                for node in manifest.nodes.values()
                if node.resource_type == NodeType.Model and node.description != ""
            ]
        )
        logger.info(f"Found {self.value} models with descriptions")
