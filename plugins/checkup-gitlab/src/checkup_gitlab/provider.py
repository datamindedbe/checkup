"""GitLab provider for checkup."""

import logging
from typing import Any, ClassVar

from checkup.provider import Provider

logger = logging.getLogger(__name__)


class GitLabProvider(Provider):
    """Provides GitLab context.

    Extracts metadata from a GitLab environment.

    Example:
        GitLabProvider()
    """

    name: ClassVar[str] = "gitlab"

    def __init__(self):
        """Initialize GitLabProvider."""
        ...

    def provide(self) -> dict[str, Any]:
        """Get GitLab environment information.

        Returns:
            Dict with GitLab metadata.
        """
        logger.info("Getting GitLab environment info")

        return {}
