import os
from typing import Any, ClassVar

from checkup.provider import Provider


class ConveyorProvider(Provider):
    name: ClassVar[str] = "ConveyorProvider"

    def provide(self) -> dict[str, Any]:
        return {
            'api_key': self.api_key,
            'environment_name': self.environment_name,
            'project_name': self.project_name
        }

    def __init__(self, project_name: str, api_key: str, environment_name: str):
        self.project_name = project_name
        self.api_key = api_key
        self.environment_name = environment_name