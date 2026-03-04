"""Airflow metrics for checkup."""

from checkup.metric import Metric
from checkup.provider import Provider
from checkup_airflow.provider import AirflowProvider


class AirflowMetric(Metric):
    """Base class for Airflow-related metrics."""

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [AirflowProvider]
