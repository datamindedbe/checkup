from checkup import Context
from checkup_conveyor import ConveyorMetric

import requests

class ConveyorLastDeploymentTime(ConveyorMetric):
    name: str = "Conveyor Last Deployment Time"
    description: str = "Time of the last deployment in Conveyor"
    unit: str = "timestamp"

    def calculate(self, context: Context, metrics: dict) -> None:
        api_key = context['conveyor_api_key']
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        r = requests.get('https://app.conveyordata.com/api/v2/projects/42d0be19-7b39-46c3-ab49-c45f197f3a32/deployments',
                     headers=headers).json()
        self.value = r['deployment'][0]['deployedOn']