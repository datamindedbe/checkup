from collections import defaultdict
from collections.abc import Sequence
from typing import Any, Literal

from checkup.measurement import Measurement
from checkup.metric import Unit

TableColumn = Literal["name", "description", "value", "unit", "diagnostics"]

ALL_COLUMNS: tuple[TableColumn, ...] = (
    "name",
    "description",
    "value",
    "unit",
    "diagnostics",
)


def effective_columns(
    columns: Sequence[TableColumn] | None, pretty: bool
) -> tuple[TableColumn, ...]:
    """
    Resolve the columns to display.
    """

    if columns is not None:
        return tuple(columns)
    if pretty:
        # Pretty output folds the unit into the value.
        return tuple(column for column in ALL_COLUMNS if column != "unit")
    return ALL_COLUMNS


def format_value_pretty(value: Any, unit: str) -> str:
    """
    Format a measurement value for presentation.
    """

    if value is None:
        return ""
    if unit == Unit.BOOLEAN:
        return "✓" if value else "✗"
    if isinstance(value, int | float) and not isinstance(value, bool):
        number = f"{value:g}" if isinstance(value, float) else str(value)
        if unit == Unit.PERCENT:
            return f"{number}%"
        return f"{number} {unit}".strip() if unit else number
    # We assume that for non-numeric values, appending the unit is not desirable.
    return str(value)


def render_cell(
    measurement: Measurement,
    column: TableColumn,
    columns: Sequence[TableColumn],
    pretty: bool,
) -> str:
    """
    Render one table cell as plain text.
    """

    metric = measurement.metric
    match column:
        case "name":
            return metric.name
        case "description":
            # Without a name column, an empty description leaves the row unidentifiable.
            if "name" not in columns and not metric.description:
                return metric.name
            return metric.description
        case "value":
            if pretty:
                return format_value_pretty(measurement.value, metric.unit)
            return str(measurement.value) if measurement.value is not None else ""
        case "unit":
            return metric.unit
        case "diagnostics":
            return measurement.diagnostic


def group_measurements_by_tags(
    measurements: list[Measurement],
    tag1: str,
    tag2: str,
    default_value: str = "Unknown",
) -> dict[tuple[str, str], list[Measurement]]:
    """Group measurements by two tag values.

    Args:
        measurements: List of measurements to group
        tag1: First tag name for grouping
        tag2: Second tag name for grouping
        default_value: Value to use when tag is missing

    Returns:
        Dict mapping (tag1_value, tag2_value) tuples to measurement lists
    """
    groups: dict[tuple[str, str], list[Measurement]] = {}
    for measurement in measurements:
        tag1_value = measurement.tags.get(tag1, default_value)
        tag2_value = measurement.tags.get(tag2, default_value)
        key = (tag1_value, tag2_value)

        if key not in groups:
            groups[key] = []
        groups[key].append(measurement)

    return groups


def group_measurements_hierarchical(
    measurements: list[Measurement],
    tag1: str,
    tag2: str,
    default_value: str = "Ungrouped",
) -> dict[str, dict[str, list[Measurement]]]:
    """Group measurements hierarchically by two tag values.

    Args:
        measurements: List of measurements to group
        tag1: First tag name for top-level grouping
        tag2: Second tag name for nested grouping
        default_value: Value to use when tag is missing

    Returns:
        Nested dict: {tag1_value: {tag2_value: [measurements]}}
    """
    grouped: dict[str, dict[str, list[Measurement]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for measurement in measurements:
        group1_value = measurement.tags.get(tag1, default_value)
        group2_value = measurement.tags.get(tag2, default_value)
        grouped[group1_value][group2_value].append(measurement)

    return dict(grouped)
