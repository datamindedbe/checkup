from typing import ClassVar

from checkup_dbt.manifest_query import output_column_missing_data_type
from checkup_dbt.metrics.base import CountTarget, DbtDiagnosticMetric


class DbtOutputColumnsWithoutDataTypeMetric(DbtDiagnosticMetric):
    name: ClassVar[str] = "dbt_output_columns_without_data_type"
    description: ClassVar[str] = "Number of columns in output models without data type"
    unit: ClassVar[str] = "columns"
    predicate = output_column_missing_data_type
    diagnostic_prefix: ClassVar[str] = "Output columns without data type"
    log_message: ClassVar[str] = "Found {value} output columns without data type"
    count_target: ClassVar[CountTarget] = CountTarget.COLUMNS
