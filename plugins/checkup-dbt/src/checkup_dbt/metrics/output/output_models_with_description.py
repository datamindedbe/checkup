import logging
from typing import ClassVar

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.metrics.output.output_models import is_output_model
from checkup_dbt.provider import DbtManifestProvider

logger = logging.getLogger(__name__)


class DbtOutputModelsWithDescriptionMetric(DbtMetric):
    name: ClassVar[str] = "dbt_output_models_with_description"
    description: ClassVar[str] = "Number of output models with descriptions"
    unit: ClassVar[str] = "models"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context[DbtManifestProvider.name]["manifest"]
        self.value = len(
            [
                node
                for node in manifest.nodes.values()
                if is_output_model(node) and node.description != ""
            ]
        )
        logger.info(f"Found {self.value} output models with descriptions")
