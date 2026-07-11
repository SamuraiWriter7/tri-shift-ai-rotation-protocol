#!/usr/bin/env python3
"""Validate Tri-Shift AI Rotation Protocol examples."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT_DIR = Path(__file__).resolve().parents[1]

VALIDATION_TARGETS = [
    {
        "name": "Shift State Record",
        "schema": ROOT_DIR / "schemas" / "shift-state-record.schema.json",
        "example": ROOT_DIR / "examples" / "shift-state-record.example.yaml",
    }
]


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON document."""

    try:
        with path.open("r", encoding="utf-8") as file:
            document = json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}"
        ) from exc

    if not isinstance(document, dict):
        raise RuntimeError(f"Expected a JSON object in {path}")

    return document


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML document."""

    try:
        with path.open("r", encoding="utf-8") as file:
            document = yaml.safe_load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"YAML file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(document, dict):
        raise RuntimeError(f"Expected a YAML mapping in {path}")

    return document


def format_error_path(error: Any) -> str:
    """Convert a jsonschema error path to a readable string."""

    if not error.absolute_path:
        return "<root>"

    return ".".join(str(part) for part in error.absolute_path)


def validate_target(
    name: str,
    schema_path: Path,
    example_path: Path,
) -> bool:
    """Validate one example against one schema."""

    print(f"[validate] {name}")
    print(f"  schema : {schema_path.relative_to(ROOT_DIR)}")
    print(f"  example: {example_path.relative_to(ROOT_DIR)}")

    schema = load_json(schema_path)
    example = load_yaml(example_path)

    Draft202012Validator.check_schema(schema)

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )

    errors = sorted(
        validator.iter_errors(example),
        key=lambda error: list(error.absolute_path),
    )

    if errors:
        for error in errors:
            location = format_error_path(error)
            print(f"[error] {location}: {error.message}")

        return False

    print(f"[ok] {example_path.name} is valid")
    return True


def main() -> int:
    """Run all validations."""

    print("=== Tri-Shift AI Rotation Protocol Validation ===")
    print()

    all_valid = True

    try:
        for target in VALIDATION_TARGETS:
            valid = validate_target(
                name=target["name"],
                schema_path=target["schema"],
                example_path=target["example"],
            )

            all_valid = all_valid and valid
            print()

    except RuntimeError as exc:
        print(f"[fatal] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"[fatal] Unexpected validation failure: {exc}", file=sys.stderr)
        return 2

    if not all_valid:
        print("Validation failed.")
        return 1

    print("All examples are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
