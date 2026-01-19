from typing import ClassVar

from checkup_dbt.manifest_query import is_output_model
from checkup_dbt.metrics.base import DbtDiagnosticMetric


def _is_output_model_without_contract(node) -> bool:
    return is_output_model(node) and not node.contract.enforced


class DbtOutputModelsWithoutContractsMetric(DbtDiagnosticMetric):
    name: ClassVar[str] = "dbt_output_models_without_contracts"
    description: ClassVar[str] = "Number of output models without enforced contracts"
    unit: ClassVar[str] = "models"
    node_predicate = _is_output_model_without_contract
    diagnostic_prefix: ClassVar[str] = "Output models without enforced contracts"
    log_message: ClassVar[str] = "Found {value} output models without contracts"
