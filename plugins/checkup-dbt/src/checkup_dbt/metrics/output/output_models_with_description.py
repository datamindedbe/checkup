import logging

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.metrics.output.output_models import is_output_model

logger = logging.getLogger(__name__)


class DbtOutputModelsWithDescriptionMetric(DbtMetric):
    name: str = "dbt_output_models_with_description"
    description: str = "Number of output models with descriptions"
    unit: str = "models"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context["dbt_manifest"]
        self.value = len(
            [
                node
                for node in manifest.nodes.values()
                if is_output_model(node) and node.description != ""
            ]
        )
        logger.info(f"Found {self.value} output models with descriptions")
