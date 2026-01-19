from typing import ClassVar

from checkup_dbt.manifest_query import is_output_model
from checkup_dbt.metrics.base import DbtNodeCountMetric

# Re-export for backward compatibility
__all__ = ["DbtOutputModelsMetric", "is_output_model"]


class DbtOutputModelsMetric(DbtNodeCountMetric):
    name: ClassVar[str] = "dbt_output_models"
    description: ClassVar[str] = "Number of output models (non-internal schema)"
    unit: ClassVar[str] = "models"
    node_predicate = is_output_model
    log_message: ClassVar[str] = "Found {value} output models"
