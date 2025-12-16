from typing import ClassVar

from checkup import Context
from checkup_conveyor import ConveyorMetric

import requests

class ConveyorLastDeploymentTime(ConveyorMetric):
    name: ClassVar[str] = "Conveyor Last Deployment Time"
    description: ClassVar[str] = "Time of the last deployment in Conveyor"
    unit: ClassVar[str] = "timestamp"
    diagnostic: str = 'Deploy the project again to update this value.'

    def calculate(self, context: Context, metrics: dict) -> None:
        proj_id = self.get_conveyor_project_id(context)
        r = requests.get(f'{self.base_url}/projects/{proj_id}/deployments',
                     headers=self.get_conveyor_api_headers(context)).json()
        self.value = r['deployment'][0]['deployedOn']


class ConveyorIsDirtyDeployment(ConveyorMetric):
    name: ClassVar[str] = "Conveyor Is Dirty Deployment"
    description: ClassVar[str] = "True if the last deployment was dirty"
    unit: ClassVar[str] = "boolean"
    diagnostic: str = 'Commit changes to git, and deploy the project again.'

    def calculate(
        self, context: Context, metrics: dict
    ) -> None:
        proj_id = self.get_conveyor_project_id(context)
        r = requests.get(f'{self.base_url}/projects/{proj_id}/builds',
                     headers=self.get_conveyor_api_headers(context)).json()
        self.value = r['builds'][0]['gitHash'].endswith('.dirty')


class ConveyorLastRunStatus(ConveyorMetric):
    name: ClassVar[str] = "Conveyor Last Run Status"
    description: ClassVar[str] = "Status of the last run in Conveyor"
    unit: ClassVar[str] = "string"


    def calculate(self, context: Context, metrics: dict) -> None:
        proj_id = self.get_conveyor_project_id(context)
        env_id = self.get_environment_id(context)
        r = requests.get(f'{self.base_url}/environments/{env_id}/application_runs',
                         params={'sortedOn': 'SortedOn_None', 'sortedOrder': 'SortedOrder_None', 'projectId': proj_id},
                     headers=self.get_conveyor_api_headers(context)).json()
        self.value = r['applicationRuns'][0]['phase']