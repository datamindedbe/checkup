import logging
from typing import ClassVar

from dbt.artifacts.resources.types import NodeType

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.provider import DbtManifestProvider

logger = logging.getLogger(__name__)


class DbtModelsWithDescriptionMetric(DbtMetric):
    name: ClassVar[str] = "dbt_models_with_description"
    description: ClassVar[str] = "Number of models with descriptions"
    unit: ClassVar[str] = "models"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context[DbtManifestProvider.name]["manifest"]
        self.value = len(
            [
                node
                for node in manifest.nodes.values()
                if node.resource_type == NodeType.Model and node.description != ""
            ]
        )
        logger.info(f"Found {self.value} models with descriptions")
