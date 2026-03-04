"""GitLab metrics for checkup."""

from checkup.metric import Metric
from checkup.provider import Provider
from checkup_gitlab.provider import GitLabProvider


class GitLabMetric(Metric):
    """Base class for GitLab-related metrics."""

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [GitLabProvider]
