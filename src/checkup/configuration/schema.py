"""
JSON Schema generation for checkup.yaml.
"""

import inspect
import json
from pathlib import Path
from typing import Any, get_origin, get_type_hints

from checkup.registry import get_registry

SCHEMA_VERSION = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID = "https://checkup.dev/schemas/checkup.yaml.json"


def _get_pydantic_schema(cls: type) -> dict | None:
    """
    Get JSON schema from a Pydantic model.
    """

    if not hasattr(cls, "model_json_schema"):
        return None

    try:
        schema = cls.model_json_schema()

        # Remove Pydantic metadata we don't need in the config schema
        schema.pop("$defs", None)  # Inline type definitions
        schema.pop("title", None)  # We use entry point names, not class names

        if not schema.get("properties"):
            return None

        return schema
    except Exception:
        return None


def _python_type_to_json_schema_type(hint: type) -> str:
    """
    Map a Python type hint to a JSON Schema type.
    """

    origin = get_origin(hint)
    if origin is not None:
        # For Union types, just use string as fallback
        return "string"

    if hint is str:
        return "string"
    if hint is int:
        return "integer"
    if hint is float:
        return "number"
    if hint is bool:
        return "boolean"
    if hint is Path or (isinstance(hint, type) and issubclass(hint, Path)):
        return "string"

    return "string"


def _get_provider_schema(cls: type) -> dict | None:
    """
    Get JSON schema for a provider from its __init__ signature.
    """

    try:
        sig = inspect.signature(cls.__init__)
        hints = get_type_hints(cls.__init__)
    except Exception:
        return None

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name == "self":
            continue

        prop: dict[str, Any] = {}

        if name in hints:
            prop["type"] = _python_type_to_json_schema_type(hints[name])
        else:
            prop["type"] = "string"

        if param.default is not inspect.Parameter.empty:
            default = param.default
            # Convert Path to string for JSON
            if hasattr(default, "__fspath__"):
                default = str(default)
            prop["default"] = default
        else:
            required.append(name)

        properties[name] = prop

    if not properties:
        return None

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required

    return schema


def _build_oneof_schema(
    names: list[str],
    schemas: dict[str, dict],
    key_field: str = "name",
) -> dict[str, Any]:
    """
    Build a oneOf schema for a list of named items.
    """

    variants = []
    for name in names:
        variant: dict[str, Any] = {
            "type": "object",
            "properties": {key_field: {"const": name}},
            "required": [key_field],
            "additionalProperties": False,
        }
        if name in schemas and "properties" in schemas[name]:
            variant["properties"].update(schemas[name]["properties"])
        variants.append(variant)

    return {"oneOf": variants} if variants else {"type": "object"}


def _collect_schemas(
    items: dict[str, type],
    schema_fn: callable,
) -> tuple[list[str], dict[str, dict]]:
    """
    Collect schemas for a dict of named classes.
    """

    names = sorted(items.keys())
    schemas = {}
    for name, cls in items.items():
        schema = schema_fn(cls)
        if schema:
            schemas[name] = schema
    return names, schemas


def generate_schema() -> dict:
    """
    Generate JSON schema for checkup.yaml configuration.

    Dynamically includes available providers, metrics, and materializers
    using Pydantic's schema generation.
    """

    registry = get_registry()

    provider_names, provider_schemas = _collect_schemas(
        registry.providers, _get_provider_schema
    )
    metric_names, metric_schemas = _collect_schemas(
        registry.metrics, _get_pydantic_schema
    )
    materializer_names, materializer_schemas = _collect_schemas(
        registry.materializers, _get_pydantic_schema
    )

    return {
        "$schema": SCHEMA_VERSION,
        "$id": SCHEMA_ID,
        "title": "Checkup Configuration",
        "description": "Configuration file for checkup",
        "type": "object",
        "properties": {
            "tags": {
                "type": "object",
                "description": "Tags to identify the data product (e.g., product, team)",
                "additionalProperties": {"type": "string"},
            },
            "providers": {
                "type": "array",
                "description": "Data providers for context enrichment",
                "items": _build_oneof_schema(provider_names, provider_schemas),
            },
            "metrics": {
                "type": "array",
                "description": "Metrics to calculate",
                "items": _build_oneof_schema(metric_names, metric_schemas),
            },
            "materializer": _build_oneof_schema(
                materializer_names, materializer_schemas, key_field="type"
            ),
        },
        "additionalProperties": False,
    }


def write_schema(output_path: Path) -> None:
    """
    Write JSON schema to file.
    """

    schema = generate_schema()
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
        f.write("\n")
