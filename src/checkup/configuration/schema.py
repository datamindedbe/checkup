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


def generate_schema() -> dict:
    """
    Generate JSON schema for checkup.yaml configuration.

    Dynamically includes available providers, metrics, and materializers
    using Pydantic's schema generation.
    """

    registry = get_registry()

    # Collect provider info
    provider_names = sorted(registry.providers.keys())
    provider_schemas = {}
    for name, cls in registry.providers.items():
        schema = _get_provider_schema(cls)
        if schema:
            provider_schemas[name] = schema

    # Collect metric info
    metric_names = sorted(registry.metrics.keys())
    metric_schemas = {}
    for name, cls in registry.metrics.items():
        schema = _get_pydantic_schema(cls)
        if schema:
            metric_schemas[name] = schema

    # Collect materializer info
    materializer_names = sorted(registry.materializers.keys())
    materializer_schemas = {}
    for name, cls in registry.materializers.items():
        schema = _get_pydantic_schema(cls)
        if schema:
            materializer_schemas[name] = schema

    # Build provider item schema with oneOf for each provider
    provider_variants = []
    for name in provider_names:
        variant: dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {"const": name},
            },
            "required": ["name"],
            "additionalProperties": False,
        }
        if name in provider_schemas and "properties" in provider_schemas[name]:
            variant["properties"].update(provider_schemas[name]["properties"])
        provider_variants.append(variant)

    provider_item_schema: dict[str, Any] = (
        {"oneOf": provider_variants} if provider_variants else {"type": "object"}
    )

    # Build metric item schema with oneOf for each metric
    metric_variants = []
    for name in metric_names:
        variant: dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {"const": name},
            },
            "required": ["name"],
            "additionalProperties": False,
        }
        if name in metric_schemas and "properties" in metric_schemas[name]:
            variant["properties"].update(metric_schemas[name]["properties"])
        metric_variants.append(variant)

    metric_item_schema: dict[str, Any] = (
        {"oneOf": metric_variants} if metric_variants else {"type": "object"}
    )

    # Build materializer schema
    materializer_props: dict[str, Any] = {
        "type": {
            "type": "string",
            "enum": materializer_names,
        }
        if materializer_names
        else {"type": "string"}
    }

    # Add properties from all materializers
    for schema in materializer_schemas.values():
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if prop_name not in materializer_props:
                    materializer_props[prop_name] = prop_schema

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
                "items": provider_item_schema,
            },
            "metrics": {
                "type": "array",
                "description": "Metrics to calculate",
                "items": metric_item_schema,
            },
            "materializer": {
                "type": "object",
                "description": "Output materializer configuration",
                "properties": materializer_props,
                "required": ["type"],
            },
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
