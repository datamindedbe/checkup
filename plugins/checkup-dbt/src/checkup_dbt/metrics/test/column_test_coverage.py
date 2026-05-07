import logging

from checkup.measurement import Measurement, Measurements
from checkup.metric import Metric
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

    name: str = "dbt_column_test_coverage"
    description: str = "Percentage of columns with at least one test"
    unit: str = "percent"

    @classmethod
    def depends_on(cls) -> list[type[Metric]]:
        return [DbtTestedColumnsMetric, DbtColumnsMetric]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        tested = measurements.get(DbtTestedColumnsMetric).value
        total = measurements.get(DbtColumnsMetric).value

        if total > 0:
            value = int(tested / total * 100)
        else:
            value = 0

        logger.info(f"Column test coverage: {value}%")
        return self.measure(value=value)
