from typing import Any, ClassVar

from checkup_dbt.manifest_query import is_output_model
from checkup_dbt.metrics.base import DbtDiagnosticMetric


def output_model_without_contract(node: Any) -> bool:
    """Check if node is an output model without an enforced contract."""
    return is_output_model(node) and not node.contract.enforced


class DbtOutputModelsWithoutContractsMetric(DbtDiagnosticMetric):
    name: ClassVar[str] = "dbt_output_models_without_contracts"
    description: ClassVar[str] = "Number of output models without enforced contracts"
    unit: ClassVar[str] = "models"
    predicate = output_model_without_contract
    diagnostic_prefix: ClassVar[str] = "Output models without enforced contracts"
    log_message: ClassVar[str] = "Found {value} output models without contracts"
