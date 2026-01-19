"""Tests for CheckUp.with_providers() method."""

from typing import Any, ClassVar

from checkup.hub import CheckUp
from checkup.provider import Provider
from checkup.providers.tags import TagProvider


class SimpleProvider(Provider):
    """Test provider with simple data."""

    name: ClassVar[str] = "simple"

    def __init__(self, value: int = 10):
        self.value = value

    def provide(self) -> dict[str, Any]:
        return {"value": self.value}


class TestWithProviders:
    """Tests for with_providers method."""

    def test_with_providers_stores_provider_sets(self):
        """Test that with_providers stores provider sets."""
        hub = CheckUp().with_providers(
            [
                [SimpleProvider(value=1)],
                [SimpleProvider(value=2)],
            ]
        )

        assert len(hub._provider_sets) == 2
        assert hub._provider_sets[0][0].value == 1
        assert hub._provider_sets[1][0].value == 2

    def test_with_providers_accepts_iterables(self):
        """Test that with_providers accepts any iterables."""
        hub = CheckUp().with_providers(
            [
                (SimpleProvider(), TagProvider(env="prod")),
            ]
        )

        assert len(hub._provider_sets) == 1
        assert len(hub._provider_sets[0]) == 2

    def test_with_providers_returns_self(self):
        """Test that with_providers returns self for chaining."""
        hub = CheckUp()
        result = hub.with_providers([[SimpleProvider()]])
        assert result is hub

    def test_with_providers_accumulates(self):
        """Test that multiple with_providers calls accumulate."""
        hub = (
            CheckUp()
            .with_providers([[SimpleProvider(value=1)]])
            .with_providers([[SimpleProvider(value=2)]])
        )

        assert len(hub._provider_sets) == 2
