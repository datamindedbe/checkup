import logging

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.metrics.output.output_models import is_output_model

logger = logging.getLogger(__name__)


class DbtOutputModelsWithoutContractsMetric(DbtMetric):
    name: str = "dbt_output_models_without_contracts"
    description: str = "Number of output models without enforced contracts"
    unit: str = "models"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context["dbt_manifest"]
        self.value = len(
            [
                node
                for node in manifest.nodes.values()
                if is_output_model(node) and not node.contract.enforced
            ]
        )
        logger.info(f"Found {self.value} output models without contracts")
