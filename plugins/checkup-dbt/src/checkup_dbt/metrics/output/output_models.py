from typing import ClassVar

from checkup_dbt.manifest_query import is_output_model
from checkup_dbt.metrics.base import DbtCountMetric


class DbtOutputModelsMetric(DbtCountMetric):
    name: str = "dbt_output_models"
    description: str = "Number of output models (non-internal schema)"
    unit: str = "models"
    predicate = is_output_model
    log_message: ClassVar[str] = "Found {value} output models"
