"""Tests for provider collection and execution (internal CheckHub methods)."""
from checkup.hub import CheckHub
from checkup.types import Context
from conftest import DummyMetric, ProviderDummyMetric, dummy_provider


# =============================================================================
# _collect_providers tests
# =============================================================================


def test_collect_providers_empty_for_metrics_without_providers():
    """Test collecting providers from metrics with no providers."""
    hub = CheckHub()
    providers = hub._collect_providers([DummyMetric])

    assert providers == []


def test_collect_providers_single_metric():
    """Test collecting providers from one metric."""
    hub = CheckHub()
    providers = hub._collect_providers([ProviderDummyMetric])

    assert providers == [dummy_provider]


def test_collect_providers_deduplication():
    """Test that duplicate providers are deduplicated."""

    class AnotherProviderMetric(ProviderDummyMetric):
        name: str = "another_provider"

    hub = CheckHub()
    providers = hub._collect_providers([ProviderDummyMetric, AnotherProviderMetric])

    assert len(providers) == 1
    assert providers[0] is dummy_provider


def test_collect_providers_mixed_metrics():
    """Test collecting from mix of metrics with and without providers."""
    hub = CheckHub()
    providers = hub._collect_providers([DummyMetric, ProviderDummyMetric])

    assert providers == [dummy_provider]


# =============================================================================
# _execute_providers tests
# =============================================================================


def test_execute_providers_empty():
    """Test executing no providers."""
    hub = CheckHub()
    context = {"initial": "data"}
    result = hub._execute_providers([], context)

    assert result == {"initial": "data"}


def test_execute_providers_single():
    """Test executing a single provider."""
    hub = CheckHub()
    context: Context = {}
    result = hub._execute_providers([dummy_provider], context)

    assert result == {"dummy_data": 100}


def test_execute_providers_multiple():
    """Test executing multiple providers."""

    def provider_a(ctx: Context) -> Context:
        return {**ctx, "a": 1}

    def provider_b(ctx: Context) -> Context:
        return {**ctx, "b": 2}

    hub = CheckHub()
    context: Context = {}
    result = hub._execute_providers([provider_a, provider_b], context)

    assert result == {"a": 1, "b": 2}


def test_execute_providers_chained():
    """Test that providers receive context from previous providers."""

    def provider_a(ctx: Context) -> Context:
        return {**ctx, "a": 1}

    def provider_b(ctx: Context) -> Context:
        return {**ctx, "b": ctx.get("a", 0) + 10}

    hub = CheckHub()
    context: Context = {}
    result = hub._execute_providers([provider_a, provider_b], context)

    assert result == {"a": 1, "b": 11}
