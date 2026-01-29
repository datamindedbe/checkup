from typing import ClassVar

from checkup_dbt.manifest_query import is_output_model
from checkup_dbt.metrics.base import CountTarget, DbtDiagnosticMetric


class DbtOutputColumnsWithoutDataTypeMetric(DbtDiagnosticMetric):
    name: ClassVar[str] = "dbt_output_columns_without_data_type"
    description: ClassVar[str] = "Number of columns in output models without data type"
    unit: ClassVar[str] = "columns"
    predicate = staticmethod(
        lambda n, _name, col: is_output_model(n) and col.data_type is None
    )
    diagnostic_prefix: ClassVar[str] = "Output columns without data type"
    log_message: ClassVar[str] = "Found {value} output columns without data type"
    count_target: ClassVar[CountTarget] = CountTarget.COLUMNS
