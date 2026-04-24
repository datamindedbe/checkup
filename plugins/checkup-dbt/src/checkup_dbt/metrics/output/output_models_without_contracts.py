from typing import ClassVar

from checkup_dbt.manifest_query import is_output_model
from checkup_dbt.metrics.base import DbtDiagnosticMetric


class DbtOutputModelsWithoutContractsMetric(DbtDiagnosticMetric):
    name: str = "dbt_output_models_without_contracts"
    description: str = "Number of output models without enforced contracts"
    unit: str = "models"
    predicate = staticmethod(lambda n: is_output_model(n) and not n.contract.enforced)
    diagnostic_prefix: ClassVar[str] = "Output models without enforced contracts"
    log_message: ClassVar[str] = "Found {value} output models without contracts"
