from checkup import CheckHub
from checkup_conveyor import ConveyorProvider
from checkup_conveyor.conveyor_metric import (
    ConveyorLastDeploymentTime,
    ConveyorIsDirtyDeployment,
    ConveyorLastRunStatus,
)


def test_conveyor_integration():
    r = (
        CheckHub()
        .with_metrics(
            [
                ConveyorLastDeploymentTime,
                ConveyorIsDirtyDeployment,
                ConveyorLastRunStatus,
            ]
        )
        .with_providers([[ConveyorProvider(project_name="activity-centers")]])
        .measure()
    )
    assert r is not None
