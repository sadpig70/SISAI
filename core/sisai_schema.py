#!/usr/bin/env python3
"""SISAI schema enforcement — schemas/*.json as a *checked* contract (stdlib only).

Determinism boundary (same pattern as skills' optional deps): if `jsonschema` is
installed it is used (full draft-07); otherwise a deterministic stdlib subset
walker validates the keywords the SISAI schemas actually use — type (incl.
["string","null"] unions), required, properties, items, enum, minimum, maximum.
`schema_features()` flags anything out of subset so a schema change can't silently
outrun the walker.
"""

import json
import os
import re

_TYPE_OK = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}

_SUPPORTED = {
    "$schema", "$id", "title", "description", "type", "required", "properties",
    "items", "enum", "minimum", "maximum", "pattern",
}


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _type_matches(value, type_spec) -> bool:
    types = type_spec if isinstance(type_spec, list) else [type_spec]
    return any(_TYPE_OK.get(t, lambda v: True)(value) for t in types)


def _walk(value, schema, path, problems):
    t = schema.get("type")
    if t is not None and not _type_matches(value, t):
        problems.append(f"{path}: expected type {t}, got {type(value).__name__}")
        return
    if "enum" in schema and value not in schema["enum"]:
        problems.append(f"{path}: {value!r} not in enum {schema['enum']}")
    if isinstance(value, str) and "pattern" in schema:
        if re.search(schema["pattern"], value) is None:
            problems.append(f"{path}: {value!r} does not match pattern {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            problems.append(f"{path}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            problems.append(f"{path}: {value} > maximum {schema['maximum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                problems.append(f"{path}: missing required key '{key}'")
        props = schema.get("properties", {})
        for key in sorted(value):
            if key in props:
                _walk(value[key], props[key], f"{path}.{key}", problems)
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            _walk(item, schema["items"], f"{path}[{i}]", problems)


def schema_features(schema: dict) -> dict:
    """{in_subset: bool, unsupported: [keyword,...]} — keys of `properties` maps are
    property names, not keywords, so they are not flagged."""
    unsupported = set()

    def scan_schema(node):
        if not isinstance(node, dict):
            return
        for k, v in node.items():
            if k not in _SUPPORTED and not k.startswith("$"):
                unsupported.add(k)
            if k in ("properties", "definitions", "patternProperties"):
                if isinstance(v, dict):
                    for sub in v.values():
                        scan_schema(sub)
            elif k == "items":
                for sub in (v if isinstance(v, list) else [v]):
                    scan_schema(sub)
            elif k in ("additionalProperties", "not"):
                scan_schema(v)
            elif k in ("allOf", "anyOf", "oneOf"):
                if isinstance(v, list):
                    for sub in v:
                        scan_schema(sub)

    scan_schema(schema)
    return {"in_subset": not unsupported, "unsupported": sorted(unsupported)}


def validate_against_schema(doc, schema) -> list:
    """Validate doc against a draft-07 schema (path str or parsed dict).
    Uses jsonschema if installed, else the deterministic stdlib subset walker."""
    if isinstance(schema, str):
        schema = _load_json(schema)
    try:
        import jsonschema
        return [f"$.{'.'.join(str(p) for p in e.absolute_path)}: {e.message}"
                for e in sorted(jsonschema.Draft7Validator(schema).iter_errors(doc),
                                key=lambda e: list(e.absolute_path))]
    except ImportError:
        problems = []
        _walk(doc, schema, "$", problems)
        return problems


def schema_path(root: str, name: str) -> str:
    """Absolute path to a shipped schema (e.g. name='threat')."""
    return os.path.join(root, "schemas", f"{name}.schema.json")
