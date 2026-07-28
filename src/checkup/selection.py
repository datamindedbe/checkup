"""
Metric selection for filtering materialized output.

Selection filters which measurements get materialized, it never changes what
is calculated, dependencies are always computed.

A selector is a set of whitespace-separated atoms (a union).
Each atom is ``[method:]pattern`` where:

- ``method`` is ``name`` (the default), ``tag`` or ``type``
- ``pattern`` supports ``*`` wildcards

Examples::

    healthcheck_*
    name:healthcheck_*
    tag:healthcheck
    type:git_tracked_file_count tag:healthcheck
"""

import fnmatch
from collections.abc import Callable, Iterable
from enum import StrEnum
from typing import assert_never

from checkup.metric import Metric


class SelectionMethod(StrEnum):
    NAME = "name"
    TAG = "tag"
    TYPE = "type"


# Resolves a metric instance to its registered type name.
# Names are needed by the filter, with a resolver being offered as argument
# because the name-type mapping is defined by the config.
TypeResolver = Callable[[Metric], str | None]


def select_metrics(
    metrics: Iterable[Metric],
    select: str | None = None,
    exclude: str | None = None,
    type_resolver: TypeResolver | None = None,
) -> set[str]:
    """
    Return the names of the metrics whose measurements should be materialized.

    With no ``select`` every metric is included;
    ``exclude`` (if given) is then removed from the set.
    """

    metrics = list(metrics)
    type_resolver = type_resolver or (lambda _name: None)

    if select:
        selected = _match_selector(select, metrics, type_resolver)
    else:
        selected = {metric.name for metric in metrics}

    if exclude:
        selected -= _match_selector(exclude, metrics, type_resolver)

    return selected


def _match_selector(
    selector: str,
    metrics: list[Metric],
    type_resolver: TypeResolver,
) -> set[str]:
    atoms = selector.split()
    return {
        metric.name
        for metric in metrics
        if any(_match_atom(atom, metric, type_resolver) for atom in atoms)
    }


def _match_atom(
    atom: str,
    metric: Metric,
    type_resolver: TypeResolver,
    *,
    default_method: SelectionMethod = SelectionMethod.NAME,
) -> bool:
    method_name, separator, pattern = atom.partition(":")
    if not separator:
        method, pattern = default_method, atom
    else:
        method = SelectionMethod(method_name)

    match method:
        case SelectionMethod.NAME:
            return fnmatch.fnmatch(metric.name, pattern)
        case SelectionMethod.TAG:
            return any(fnmatch.fnmatch(tag, pattern) for tag in metric.tags)
        case SelectionMethod.TYPE:
            metric_type = type_resolver(metric)
            return metric_type is not None and fnmatch.fnmatch(metric_type, pattern)
        case _:
            assert_never(method)
