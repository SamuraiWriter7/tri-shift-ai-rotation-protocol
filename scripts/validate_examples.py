#!/usr/bin/env python3
"""Validate Tri-Shift AI Rotation Protocol examples."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT_DIR = Path(__file__).resolve().parents[1]

VALIDATION_TARGETS = [
    {
        "name": "Shift State Record",
        "schema": ROOT_DIR / "schemas" / "shift-state-record.schema.json",
        "example": ROOT_DIR / "examples" / "shift-state-record.example.yaml",
        "semantic_validator": None,
    },
    {
        "name": "Shift Handoff Record",
        "schema": ROOT_DIR / "schemas" / "shift-handoff-record.schema.json",
        "example": ROOT_DIR / "examples" / "shift-handoff-record.example.yaml",
        "semantic_validator": "validate_shift_handoff_semantics",
    },
]


class SemanticValidationError(ValueError):
    """Raised when a document violates protocol-level semantic invariants."""


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object."""

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
    """Load a YAML mapping."""

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


def parse_datetime(value: str, field_name: str) -> datetime:
    """Parse an RFC3339-like datetime value."""

    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (TypeError, ValueError) as exc:
        raise SemanticValidationError(
            f"{field_name} must be a valid date-time string"
        ) from exc


def require(condition: bool, message: str) -> None:
    """Raise a semantic validation error when a condition is false."""

    if not condition:
        raise SemanticValidationError(message)


def validate_shift_handoff_semantics(document: dict[str, Any]) -> None:
    """Validate cross-field invariants for a tri-shift handoff."""

    participants = document["participants"]

    releasing = participants["releasing_unit"]["unit_id"]
    assuming = participants["assuming_unit"]["unit_id"]
    continuity = participants["continuity_unit"]["unit_id"]

    require(
        len({releasing, assuming, continuity}) == 3,
        "participants must reference three distinct shift units",
    )

    authority = document["authority_transfer"]

    require(
        authority["previous_holder"] == releasing,
        "authority_transfer.previous_holder must match the releasing unit",
    )
    require(
        authority["next_holder"] == assuming,
        "authority_transfer.next_holder must match the assuming unit",
    )
    require(
        authority["rollback_target_unit_id"] == releasing,
        "authority_transfer.rollback_target_unit_id must match the releasing unit",
    )

    verification = document["verification"]
    continuity_guard = document["continuity_guard"]
    acceptance = document["acceptance"]

    require(
        verification["verifier_unit_id"] == continuity,
        "verification.verifier_unit_id must match the continuity unit",
    )
    require(
        continuity_guard["guarded_by_unit_id"] == continuity,
        "continuity_guard.guarded_by_unit_id must match the continuity unit",
    )

    if acceptance["status"] in {"ACCEPTED", "CONDITIONAL"}:
        require(
            acceptance["accepted_by_unit_id"] == assuming,
            "accepted_by_unit_id must match the assuming unit",
        )

    for task in document["transfer_payload"]["active_tasks"]:
        require(
            task["owner_before"] == releasing,
            f"task {task['task_id']} owner_before must match the releasing unit",
        )
        require(
            task["owner_after"] == assuming,
            f"task {task['task_id']} owner_after must match the assuming unit",
        )

    prepared_at = parse_datetime(
        document["handoff_window"]["prepared_at"],
        "handoff_window.prepared_at",
    )
    cutover_at = parse_datetime(
        document["handoff_window"]["planned_cutover_at"],
        "handoff_window.planned_cutover_at",
    )

    require(
        prepared_at <= cutover_at,
        "prepared_at must not be later than planned_cutover_at",
    )

    completed_at_value = document["handoff_window"]["completed_at"]

    if completed_at_value is not None:
        completed_at = parse_datetime(
            completed_at_value,
            "handoff_window.completed_at",
        )

        require(
            cutover_at <= completed_at,
            "completed_at must not be earlier than planned_cutover_at",
        )
        require(
            (completed_at - prepared_at).total_seconds()
            <= document["handoff_window"]["maximum_duration_seconds"],
            "handoff duration exceeds maximum_duration_seconds",
        )

    released_at_value = authority["released_at"]
    acquired_at_value = authority["acquired_at"]

    if released_at_value is not None and acquired_at_value is not None:
        released_at = parse_datetime(
            released_at_value,
            "authority_transfer.released_at",
        )
        acquired_at = parse_datetime(
            acquired_at_value,
            "authority_transfer.acquired_at",
        )

        require(
            released_at <= acquired_at,
            "primary authority must be released before or at acquisition",
        )

    if document["handoff_phase"] == "COMPLETED":
        require(
            authority["status"] == "COMPLETE",
            "a completed handoff requires authority_transfer.status COMPLETE",
        )
        require(
            verification["required_checks_passed"] is True,
            "a completed handoff requires all mandatory checks to pass",
        )
        require(
            not verification["blocking_issues"],
            "a completed handoff cannot contain verification blockers",
        )
        require(
            acceptance["status"] == "ACCEPTED",
            "a completed handoff requires explicit acceptance",
        )
        require(
            acceptance["accepted_at"] is not None,
            "a completed handoff requires accepted_at",
        )
        require(
            continuity_guard["service_status"] != "INTERRUPTED",
            "an interrupted handoff cannot be marked COMPLETED",
        )
        require(
            continuity_guard["duplicate_execution_detected"] is False,
            "a completed handoff cannot contain duplicate execution",
        )

        blocking_tasks = [
            task["task_id"]
            for task in document["transfer_payload"]["active_tasks"]
            if task["blocking"]
        ]

        blocking_risks = [
            risk["risk_id"]
            for risk in document["transfer_payload"]["risk_flags"]
            if risk["blocking"]
        ]

        require(
            not blocking_tasks,
            f"completed handoff contains blocking tasks: {blocking_tasks}",
        )
        require(
            not blocking_risks,
            f"completed handoff contains blocking risks: {blocking_risks}",
        )


SEMANTIC_VALIDATORS: dict[
    str,
    Callable[[dict[str, Any]], None],
] = {
    "validate_shift_handoff_semantics": validate_shift_handoff_semantics,
}


def validate_target(
    name: str,
    schema_path: Path,
    example_path: Path,
    semantic_validator_name: str | None,
) -> bool:
    """Validate one example against its schema and semantic invariants."""

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
            print(f"[schema-error] {location}: {error.message}")

        return False

    print("[schema-ok]")

    if semantic_validator_name is not None:
        semantic_validator = SEMANTIC_VALIDATORS[
            semantic_validator_name
        ]

        try:
            semantic_validator(example)
        except SemanticValidationError as exc:
            print(f"[semantic-error] {exc}")
            return False

        print("[semantic-ok]")

    print(f"[ok] {example_path.name} is valid")
    return True


def main() -> int:
    """Run all validation targets."""

    print("=== Tri-Shift AI Rotation Protocol Validation ===")
    print()

    all_valid = True

    try:
        for target in VALIDATION_TARGETS:
            valid = validate_target(
                name=target["name"],
                schema_path=target["schema"],
                example_path=target["example"],
                semantic_validator_name=target["semantic_validator"],
            )

            all_valid = all_valid and valid
            print()

    except RuntimeError as exc:
        print(f"[fatal] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            f"[fatal] Unexpected validation failure: {exc}",
            file=sys.stderr,
        )
        return 2

    if not all_valid:
        print("Validation failed.")
        return 1

    print("All examples are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
