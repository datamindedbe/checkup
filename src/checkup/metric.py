from abc import ABC
from collections.abc import Hashable
from typing import Any




class Metric(ABC):
    name: str
    description: str
    unit: Any
    value: Hashable
    tags: dict

    @classmethod
    def measure(cls, context: dict) -> "Metric":
        raise NotImplementedError("Subclasses must implement this method.")


class PythonMajorVersionMetric(Metric):
    name = "python_major_version"
    description = "The major version of Python"
    unit = "version"
    tags: dict = {}

    @classmethod
    def measure(cls, context: dict) -> "PythonMajorVersionMetric":
        import sys

        instance = cls()
        instance.value = float(sys.version_info.major)
        return instance
