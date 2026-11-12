"""Narrow JSON Schema checker for the frozen Receipt-v1 document.

Covers the keywords the Receipt-v1 schema uses. It is not a general validator.
"""

from __future__ import annotations

import re
from typing import Any


class SchemaError(ValueError):
    pass


def _fail(path: str, message: str) -> None:
    raise SchemaError(f"{path}: {message}")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def check(schema: dict[str, Any], instance: object, path: str = "$") -> None:
    if "enum" in schema and instance not in schema["enum"]:
        _fail(path, f"value {instance!r} is not in enum")
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(instance, dict):
            _fail(path, "expected object")
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                _fail(path, f"missing required field {key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = [key for key in instance if key not in properties]
            if extra:
                _fail(path, f"unexpected field {extra[0]}")
        for key, value in instance.items():
            if key in properties:
                check(properties[key], value, f"{path}.{key}")
        return
    if expected == "array":
        if not isinstance(instance, list):
            _fail(path, "expected array")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                check(item_schema, item, f"{path}[{index}]")
        return
    if expected == "string":
        if not isinstance(instance, str):
            _fail(path, "expected string")
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(instance) < min_length:
            _fail(path, "string shorter than minLength")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, instance) is None:
            _fail(path, f"string does not match {pattern}")
        return
    if expected == "integer":
        if not _is_int(instance):
            _fail(path, "expected integer")
        minimum = schema.get("minimum")
        if isinstance(minimum, int) and instance < minimum:
            _fail(path, f"integer below minimum {minimum}")
        return
    if expected is None and "enum" in schema:
        return
    if expected is not None:
        _fail(path, f"unsupported schema type {expected}")
