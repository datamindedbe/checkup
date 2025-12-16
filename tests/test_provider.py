"""Tests for Provider base class."""

from typing import Any, ClassVar

import pytest

from checkup.provider import Provider


class TestProviderBaseClass:
    """Tests for the Provider abstract base class."""

    def test_provider_is_abstract(self):
        """Test that Provider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Provider()

    def test_provider_subclass_must_define_name(self):
        """Test that Provider subclass must have a name attribute."""

        class NoNameProvider(Provider):
            def provide(self) -> dict[str, Any]:
                return {}

        provider = NoNameProvider()
        with pytest.raises(AttributeError):
            _ = provider.name

    def test_provider_subclass_must_implement_provide(self):
        """Test that Provider subclass must implement provide method."""

        class NoProvideProvider(Provider):
            name: ClassVar[str] = "no_provide"

        with pytest.raises(TypeError):
            NoProvideProvider()

    def test_valid_provider_subclass(self):
        """Test that a valid Provider subclass works correctly."""

        class ValidProvider(Provider):
            name: ClassVar[str] = "valid"

            def __init__(self, value: str = "default"):
                self.value = value

            def provide(self) -> dict[str, Any]:
                return {"key": self.value}

        provider = ValidProvider(value="custom")
        result = provider.provide()
        assert result == {"key": "custom"}
        assert provider.name == "valid"

    def test_provider_with_no_args(self):
        """Test provider that takes no constructor arguments."""

        class SimpleProvider(Provider):
            name: ClassVar[str] = "simple"

            def provide(self) -> dict[str, Any]:
                return {"static": "data"}

        provider = SimpleProvider()
        assert provider.provide() == {"static": "data"}
