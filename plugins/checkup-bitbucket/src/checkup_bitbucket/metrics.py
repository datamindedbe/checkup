"""Bitbucket metrics for checkup."""

from checkup.metric import Metric
from checkup.provider import Provider
from checkup_bitbucket.provider import BitbucketProvider


class BitbucketMetric(Metric):
    """Base class for Bitbucket-related metrics."""

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [BitbucketProvider]
