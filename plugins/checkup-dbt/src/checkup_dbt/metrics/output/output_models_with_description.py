from typing import ClassVar

from checkup_dbt.manifest_query import has_description, is_output_model
from checkup_dbt.metrics.base import DbtCountMetric


class DbtOutputModelsWithDescriptionMetric(DbtCountMetric):
    name: ClassVar[str] = "dbt_output_models_with_description"
    description: ClassVar[str] = "Number of output models with descriptions"
    unit: ClassVar[str] = "models"
    predicate = staticmethod(lambda n: is_output_model(n) and has_description(n))
    log_message: ClassVar[str] = "Found {value} output models with descriptions"
