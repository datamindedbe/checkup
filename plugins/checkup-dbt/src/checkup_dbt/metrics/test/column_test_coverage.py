import logging
from typing import ClassVar

from checkup.metric import Measurement, Metric
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric
from checkup_dbt.metrics.core.columns import DbtColumnsMetric
from checkup_dbt.metrics.test.tested_columns import DbtTestedColumnsMetric

logger = logging.getLogger(__name__)


class DbtColumnTestCoverageMetric(DbtMetric):
    """
    Percentage of columns with at least one test.

    This is a derived metric that depends on other metrics,
    so it implements calculate() directly.
    """

    name: ClassVar[str] = "dbt_column_test_coverage"
    description: ClassVar[str] = "Percentage of columns with at least one test"
    unit: ClassVar[str] = "percent"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [DbtTestedColumnsMetric, DbtColumnsMetric]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        tested = measurements[DbtTestedColumnsMetric].value
        total = measurements[DbtColumnsMetric].value

        if total > 0:
            value = int(tested / total * 100)
        else:
            value = 0

        logger.info(f"Column test coverage: {value}%")
        return self.measurement(value=value)
