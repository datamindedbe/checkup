from typing import ClassVar

from checkup_dbt.manifest_query import (
    has_description,
    is_output_model,
    without_description,
)
from checkup_dbt.metrics.base import DbtCountMetric


class DbtOutputModelsWithDescriptionMetric(DbtCountMetric):
    name: str = "dbt_output_models_with_description"
    description: str = "Number of output models with descriptions"
    unit: str = "models"
    predicate = staticmethod(lambda n: is_output_model(n) and has_description(n))
    log_message: ClassVar[str] = "Found {value} output models with descriptions"


class DbtOutputModelsWithoutDescriptionMetric(DbtCountMetric):
    name: str = "dbt_output_models_without_description"
    description: str = "Number of output models without descriptions"
    unit: str = "models"
    predicate = staticmethod(lambda n: is_output_model(n) and without_description(n))
    log_message: ClassVar[str] = "Found {value} output models without descriptions"
