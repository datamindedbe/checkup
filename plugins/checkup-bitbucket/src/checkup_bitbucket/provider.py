"""Bitbucket provider for checkup."""

import logging
from typing import Any, ClassVar

from checkup.provider import Provider

logger = logging.getLogger(__name__)


class BitbucketProvider(Provider):
    """Provides Bitbucket context.

    Extracts metadata from a Bitbucket environment.

    Example:
        BitbucketProvider()
    """

    name: ClassVar[str] = "bitbucket"

    def __init__(self):
        """Initialize BitbucketProvider."""
        ...

    def provide(self) -> dict[str, Any]:
        """Get Bitbucket environment information.

        Returns:
            Dict with Bitbucket metadata.
        """
        logger.info("Getting Bitbucket environment info")

        return {}
