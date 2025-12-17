import logging
from typing import ClassVar

from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.metrics.output.output_models import is_output_model
from checkup_dbt.provider import DbtManifestProvider

logger = logging.getLogger(__name__)


class DbtOutputModelsWithoutContractsMetric(DbtMetric):
    name: ClassVar[str] = "dbt_output_models_without_contracts"
    description: ClassVar[str] = "Number of output models without enforced contracts"
    unit: ClassVar[str] = "models"

    def calculate(self, context: Context, metrics: dict) -> None:
        manifest = context[DbtManifestProvider.name]["manifest"]
        models_without_contracts = [
            node.name
            for node in manifest.nodes.values()
            if is_output_model(node) and not node.contract.enforced
        ]
        self.value = len(models_without_contracts)
        if models_without_contracts:
            self.diagnostic = f"Output models without enforced contracts: {', '.join(sorted(models_without_contracts))}"
        logger.info(f"Found {self.value} output models without contracts")
