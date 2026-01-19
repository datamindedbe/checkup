from typing import ClassVar

from checkup_dbt.manifest_query import column_has_description
from checkup_dbt.metrics.base import CountTarget, DbtCountMetric


class DbtColumnsWithDescriptionMetric(DbtCountMetric):
    name: ClassVar[str] = "dbt_columns_with_description"
    description: ClassVar[str] = "Number of columns with descriptions"
    unit: ClassVar[str] = "columns"
    count_target: ClassVar[CountTarget] = CountTarget.COLUMNS
    predicate = column_has_description
    log_message: ClassVar[str] = "Found {value} columns with descriptions"
