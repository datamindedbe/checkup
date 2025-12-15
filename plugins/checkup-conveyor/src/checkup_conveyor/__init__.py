"""Python metrics for checkup."""
import os
from typing import Callable

from checkup import Context
from checkup.metric import Metric


class ConveyorMetric(Metric):
    """Base class for Conveyor-related metrics."""

    def providers(cls) -> list[Callable[[Context], Context]]:
        return [lambda context: context.update({'conveyor_api_key': os.environ['CHECKUP__CONVEYOR__API_KEY']})]
