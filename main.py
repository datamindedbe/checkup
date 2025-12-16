from checkup import CheckHub, ConsoleMaterializer
from checkup_conveyor import ConveyorProvider
from checkup_conveyor.conveyor_metric import *


if __name__ == "__main__":
    (
        CheckHub()
        .with_metrics([
                ConveyorLastDeploymentTime,
                ConveyorIsDirtyDeployment,
                ConveyorLastRunStatus,
            ])
        .with_providers([[ConveyorProvider(project_name='activity-centers')]])
        .measure()
        .materialize(ConsoleMaterializer())
    )
