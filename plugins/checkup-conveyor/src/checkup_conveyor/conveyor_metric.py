from checkup import Context
from checkup_conveyor import ConveyorMetric

import os

class ConveyorLastDeploymentTime(ConveyorMetric):
    name: str = "Conveyor Last Deployment Time"
    description: str = "Time of the last deployment in Conveyor"
    unit: str = "timestamp"

    def calculate(self, context: Context, metrics: dict) -> None:
        self.value = '2025-01-01'