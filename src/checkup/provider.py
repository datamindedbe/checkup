"""Provider base class for context enrichment."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class Provider(ABC):
    """Base class for context providers.

    Providers enrich the context with data that metrics can use.
    Each provider adds data under its own namespace in the context.

    Subclasses must:
        - Define a `name` class attribute (the namespace)
        - Implement the `provide()` instance method
        - Accept configuration in `__init__`

    Example:
        class DatabaseProvider(Provider):
            name: ClassVar[str] = "database"

            def __init__(self, connection_string: str):
                self.connection_string = connection_string

            def provide(self) -> dict[str, Any]:
                conn = connect(self.connection_string)
                return {"connection": conn}

    The framework adds the returned dict under context[provider.name].
    """

    name: ClassVar[str]

    @abstractmethod
    def provide(self) -> dict[str, Any]:
        """Generate data to add to context under this provider's namespace.

        Returns:
            Dict of data to add under context[cls.name]
        """
        ...

    def is_tag_provider(self) -> bool:
        """Return True if this provider supplies tags instead of context data.

        Tag providers have their data merged directly into metric.tags
        instead of being added to the context namespace.

        Override this method to return True in tag-providing subclasses.

        Returns:
            False by default; True for tag providers
        """
        return False
