"""Tests for TagProvider."""

from checkup.providers.tags import TagProvider


class TestTagProvider:
    """Tests for TagProvider special provider."""

    def test_tag_provider_has_correct_name(self):
        """Test TagProvider has name 'tags'."""
        provider = TagProvider(env="prod")
        assert provider.name == "tags"

    def test_tag_provider_stores_kwargs(self):
        """Test TagProvider stores kwargs as tags."""
        provider = TagProvider(env="prod", team="data")
        assert provider.tags == {"env": "prod", "team": "data"}

    def test_tag_provider_provide_returns_tags(self):
        """Test provide() returns the tags dict."""
        provider = TagProvider(env="prod", team="data")
        result = provider.provide()
        assert result == {"env": "prod", "team": "data"}

    def test_tag_provider_empty_tags(self):
        """Test TagProvider with no tags."""
        provider = TagProvider()
        assert provider.provide() == {}

    def test_tag_provider_various_value_types(self):
        """Test TagProvider accepts various value types."""
        provider = TagProvider(count=42, enabled=True, ratio=0.5)
        result = provider.provide()
        assert result == {"count": 42, "enabled": True, "ratio": 0.5}
