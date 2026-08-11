"""Small JSON validation helpers for VLM structured output."""

import json
from typing import Iterable


def validate_json_fields(raw_text: str, required_fields: Iterable[str]):
    """Parse JSON text and report required top-level field coverage."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return {
            "valid": False,
            "data": None,
            "missing_fields": list(required_fields),
            "error": f"Invalid JSON: {exc}",
        }

    missing = [field for field in required_fields if field not in data]
    return {
        "valid": len(missing) == 0,
        "data": data,
        "missing_fields": missing,
        "error": "" if not missing else f"Missing fields: {', '.join(missing)}",
    }


def _collect_missing(data, schema, prefix=""):
    missing = []
    for field in schema.get("required", []):
        if not isinstance(data, dict) or field not in data:
            missing.append(f"{prefix}{field}")
    properties = schema.get("properties", {})
    if isinstance(data, dict):
        for key, child_schema in properties.items():
            if key in data and isinstance(child_schema, dict):
                missing.extend(_collect_missing(data[key], child_schema, f"{prefix}{key}."))
    return missing


def validate_json_schema(raw_text: str, schema: dict):
    """Validate required fields in a small JSON-schema-like dictionary."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return {
            "valid": False,
            "data": None,
            "missing_fields": list(schema.get("required", [])),
            "error": f"Invalid JSON: {exc}",
        }
    missing = _collect_missing(data, schema or {})
    return {
        "valid": len(missing) == 0,
        "data": data,
        "missing_fields": missing,
        "error": "" if not missing else f"Missing fields: {', '.join(missing)}",
    }
