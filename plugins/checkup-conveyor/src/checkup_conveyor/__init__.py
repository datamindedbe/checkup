"""Python metrics for checkup."""
import os
from typing import Callable

from checkup import Context
from checkup.metric import Metric

import requests


def conveyor_context(context: Context) -> Context:
    r = context.copy()
    r.update({'conveyor_api_key': os.environ['CHECKUP__CONVEYOR__API_KEY']})
    return r


class ConveyorMetric(Metric):
    """Base class for Conveyor-related metrics."""

    @classmethod
    def providers(cls) -> list[Callable[[Context], Context]]:
        return [conveyor_context]

