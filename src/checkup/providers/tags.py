"""TagProvider for adding arbitrary tags to metrics."""

from typing import Any, ClassVar

from checkup.provider import Provider


class TagProvider(Provider):
    """
    Provider for adding tags to metrics.

    Tags are automatically merged into measurement.tags after calculation.

    Example:
        hub.with_providers([
            [DbtProvider(path="./manifest.json"), TagProvider(env="prod", team="data")]
        ])
    """

    name: ClassVar[str] = "tags"

    def __init__(self, **tags: Any):
        self.tags = tags

    def provide(self) -> dict[str, Any]:
        return self.tags
