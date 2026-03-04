"""GitHub metrics for checkup."""

from checkup.metric import Metric
from checkup.provider import Provider
from checkup_github.provider import GitHubProvider


class GitHubMetric(Metric):
    """Base class for GitHub-related metrics."""

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [GitHubProvider]
