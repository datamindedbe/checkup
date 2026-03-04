"""GitHub provider for checkup."""

import logging
from typing import Any, ClassVar

from checkup.provider import Provider

logger = logging.getLogger(__name__)


class GitHubProvider(Provider):
    """Provides GitHub context.

    Extracts metadata from a GitHub environment.

    Example:
        GitHubProvider()
    """

    name: ClassVar[str] = "github"

    def __init__(self):
        """Initialize GitHubProvider."""
        ...

    def provide(self) -> dict[str, Any]:
        """Get GitHub environment information.

        Returns:
            Dict with GitHub metadata.
        """
        logger.info("Getting GitHub environment info")

        return {}
