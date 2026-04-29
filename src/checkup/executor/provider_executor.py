"""Provider execution."""

import logging

from checkup.errors import ProviderError
from checkup.provider import Provider
from checkup.types import Context

logger = logging.getLogger(__name__)


class ProviderExecutor:
    """
    Executes providers and builds context.
    """

    def execute(
        self, provider_set: list[Provider]
    ) -> tuple[Context, list[ProviderError]]:
        """
        Execute all providers and build namespaced context.

        Each provider's data is added under its namespace (provider.name).

        Args:
            provider_set: List of provider instances

        Returns:
            Tuple of (context dict, list of errors)
        """

        context: Context = {}
        errors: list[ProviderError] = []

        for provider in provider_set:
            try:
                logger.debug("Executing provider: %s", provider.name)
                context[provider.name] = provider.provide()
                logger.debug("Provider %s completed successfully", provider.name)
            except Exception as e:
                error = ProviderError(provider, e)
                logger.error("Provider %s failed: %s", provider.name, e)
                errors.append(error)

        return context, errors
