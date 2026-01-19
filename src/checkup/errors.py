"""Exception classes for the Checkup framework."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from checkup.metric import Metric
    from checkup.provider import Provider


class ProviderError(Exception):
    """Exception raised when a provider fails during execution."""

    def __init__(self, provider: "Provider", original_error: Exception):
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"Provider '{provider.name}' failed: {original_error}")


class MetricPicklingError(Exception):
    """Exception raised when a metric cannot be pickled for process execution."""

    def __init__(self, metric_cls: "type[Metric]", original_error: Exception):
        self.metric_cls = metric_cls
        self.original_error = original_error
        super().__init__(
            f"Metric '{metric_cls.name}' cannot be pickled for process execution. "
            f"Consider using ExecutorType.THREAD instead. Original error: {original_error}"
        )


class DuplicateMetricNameError(Exception):
    """Exception raised when multiple metrics have the same name."""

    def __init__(self, name: str, metric_classes: "list[type[Metric]]"):
        self.name = name
        self.metric_classes = metric_classes
        class_names = ", ".join(cls.__name__ for cls in metric_classes)
        super().__init__(
            f"Duplicate metric name '{name}' found in classes: {class_names}. "
            f"Each metric must have a unique name."
        )
