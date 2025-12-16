from checkup import CheckHub, ConsoleMaterializer, TagProvider
from checkup_conveyor import ConveyorProvider
from checkup_conveyor.conveyor_metric import *


domains = {
    'Operations': ['Activity Centers', 'Rill Demo'],
    'Lockers': ['Ingest KSS', 'Ingest LRS', 'Lockers Aggregation']
}

providers = []
for domain, projects in domains.items():
    for project in projects:
        providers.append([TagProvider(domain=domain, project=project), ConveyorProvider(project_name=project.lower().replace(' ', '-'))])

if __name__ == "__main__":
    (
        CheckHub()
        .with_metrics([
                ConveyorLastDeploymentTime,
                ConveyorIsDirtyDeployment,
                ConveyorLastRunStatus,
            ])
        .with_providers(providers)
        .measure()
        .materialize(ConsoleMaterializer(group_tag_1='domain', group_tag_2='project'))
    )
