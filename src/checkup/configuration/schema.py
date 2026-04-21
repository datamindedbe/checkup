"""
JSON Schema generation for checkup.yaml.
"""

import json
from pathlib import Path
from typing import Any

from checkup.registry import get_registry

SCHEMA_VERSION = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID = "https://checkup.dev/schemas/checkup.yaml.json"


def _get_pydantic_schema(cls: type) -> dict | None:
    """
    Get JSON schema from a Pydantic model, filtering internal fields.
    """

    if not hasattr(cls, "model_json_schema"):
        return None

    try:
        schema = cls.model_json_schema()

        # Remove internal fields for metrics
        if "properties" in schema:
            for field in ("value", "diagnostic", "tags"):
                schema["properties"].pop(field, None)
            if "required" in schema:
                schema["required"] = [
                    r
                    for r in schema["required"]
                    if r not in ("value", "diagnostic", "tags")
                ]

        # Remove $defs if present (inline everything)
        schema.pop("$defs", None)
        schema.pop("title", None)

        if not schema.get("properties"):
            return None

        return schema
    except Exception:
        return None


def _get_provider_schema(cls: type) -> dict | None:
    """
    Get JSON schema for a provider from its __init__ signature.
    """

    import inspect
    from typing import get_type_hints

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

        # Get type
        if name in hints:
            hint = hints[name]
            type_name = getattr(hint, "__name__", str(hint))
            if "str" in type_name or "str" in str(hint):
                prop["type"] = "string"
            elif "int" in type_name:
                prop["type"] = "integer"
            elif "float" in type_name:
                prop["type"] = "number"
            elif "bool" in type_name:
                prop["type"] = "boolean"
            elif "Path" in str(hint):
                prop["type"] = "string"
            else:
                prop["type"] = "string"
        else:
            prop["type"] = "string"

        # Get default
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
