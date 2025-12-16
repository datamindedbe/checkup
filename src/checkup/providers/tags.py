"""TagProvider for adding arbitrary tags to metrics."""

from typing import Any, ClassVar

from checkup.provider import Provider


class TagProvider(Provider):
    """Special provider for adding tags to metrics.

    Unlike regular providers, TagProvider's data is auto-merged
    into metric.tags by the framework rather than added to context.

    Example:
        hub.with_providers([
            [DbtProvider(path="./manifest.json"), TagProvider(env="prod", team="data")]
        ])
    """

    name: ClassVar[str] = "tags"

    def __init__(self, **tags: Any):
        """Initialize with arbitrary key-value tags.

        Args:
            **tags: Key-value pairs to add as metric tags
        """
        self.tags = tags

    def provide(self) -> dict[str, Any]:
        """Return tags dict.

        Returns:
            Dict of tags to merge into metric.tags
        """
        return self.tags
