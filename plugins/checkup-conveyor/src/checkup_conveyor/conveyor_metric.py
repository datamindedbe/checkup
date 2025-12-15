from typing import Callable

from checkup import Context
from checkup.metric import Metric

import os

class ConveyorLastDeploymentTime(Metric):
    name: str = "Conveyor Last Deployment Time"
    description: str = "Time of the last deployment in Conveyor"
    unit: str = "timestamp"

    def providers(cls) -> list[Callable[[Context], Context]]:
        return [lambda context: context.update({'conveyor_api_key': os.environ['CHECKUP__CONVEYOR__API_KEY']})]

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = '2025-01-01'