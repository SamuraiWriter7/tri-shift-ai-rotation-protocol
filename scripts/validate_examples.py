#!/usr/bin/env python3
"""Validate Tri-Shift AI Rotation Protocol examples."""

from __future__ import annotations

import json
import math
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
    {
        "name": "Adaptive Rotation Policy",
        "schema": ROOT_DIR / "schemas" / "adaptive-rotation-policy.schema.json",
        "example": ROOT_DIR / "examples" / "adaptive-rotation-policy.example.yaml",
        "semantic_validator": "validate_rotation_policy_semantics",
    },
    {
        "name": "Rotation Evaluation Record",
        "schema": ROOT_DIR / "schemas" / "rotation-evaluation-record.schema.json",
        "example": ROOT_DIR / "examples" / "rotation-evaluation-record.example.yaml",
        "semantic_validator": "validate_rotation_evaluation_semantics",
    },
    {
    "name": "Multi-Wing Shift Matrix",
    "schema": (
        ROOT_DIR
        / "schemas"
        / "multi-wing-shift-matrix.schema.json"
    ),
    "example": (
        ROOT_DIR
        / "examples"
        / "multi-wing-shift-matrix.example.yaml"
    ),
    "semantic_validator": "validate_multi_wing_matrix_semantics",
},
   {
    "name": "Continuous Operation Receipt",
    "schema": (
        ROOT_DIR
        / "schemas"
        / "continuous-operation-receipt.schema.json"
    ),
    "example": (
        ROOT_DIR
        / "examples"
        / "continuous-operation-receipt.example.yaml"
    ),
    "semantic_validator":
        "validate_continuous_operation_receipt_semantics",
}, 
]


class SemanticValidationError(ValueError):
    """Raised when a protocol-level invariant is violated."""


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object."""

    try:
        with path.open("r", encoding="utf-8") as file:
            document = json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in {path}: "
            f"line {exc.lineno}, column {exc.colno}"
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


def parse_datetime(value: str, field_name: str) -> datetime:
    """Parse an ISO-8601 or RFC3339-like datetime."""

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise SemanticValidationError(
            f"{field_name} must be a valid date-time"
        ) from exc


def require(condition: bool, message: str) -> None:
    """Require a semantic condition."""

    if not condition:
        raise SemanticValidationError(message)


def approximately_equal(
    left: float,
    right: float,
    tolerance: float = 1e-6,
) -> bool:
    """Return whether two floating-point values are approximately equal."""

    return math.isclose(
        left,
        right,
        rel_tol=tolerance,
        abs_tol=tolerance,
    )


def format_error_path(error: Any) -> str:
    """Convert a jsonschema error path to readable text."""

    if not error.absolute_path:
        return "<root>"

    return ".".join(str(part) for part in error.absolute_path)


def validate_shift_handoff_semantics(
    document: dict[str, Any],
    context: dict[str, Any],
) -> None:
    """Validate tri-party shift handoff invariants."""

    del context

    participants = document["participants"]

    releasing = participants["releasing_unit"]["unit_id"]
    assuming = participants["assuming_unit"]["unit_id"]
    continuity = participants["continuity_unit"]["unit_id"]

    require(
        len({releasing, assuming, continuity}) == 3,
        "handoff participants must reference three distinct units",
    )

    authority = document["authority_transfer"]

    require(
        authority["previous_holder"] == releasing,
        "previous_holder must match the releasing unit",
    )
    require(
        authority["next_holder"] == assuming,
        "next_holder must match the assuming unit",
    )
    require(
        authority["rollback_target_unit_id"] == releasing,
        "rollback target must match the releasing unit",
    )

    verification = document["verification"]
    continuity_guard = document["continuity_guard"]
    acceptance = document["acceptance"]

    require(
        verification["verifier_unit_id"] == continuity,
        "verifier_unit_id must match the continuity unit",
    )
    require(
        continuity_guard["guarded_by_unit_id"] == continuity,
        "guarded_by_unit_id must match the continuity unit",
    )

    if acceptance["status"] in {"ACCEPTED", "CONDITIONAL"}:
        require(
            acceptance["accepted_by_unit_id"] == assuming,
            "accepted_by_unit_id must match the assuming unit",
        )

    for task in document["transfer_payload"]["active_tasks"]:
        require(
            task["owner_before"] == releasing,
            f"task {task['task_id']} owner_before is invalid",
        )
        require(
            task["owner_after"] == assuming,
            f"task {task['task_id']} owner_after is invalid",
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

    completed_value = document["handoff_window"]["completed_at"]

    if completed_value is not None:
        completed_at = parse_datetime(
            completed_value,
            "handoff_window.completed_at",
        )

        require(
            cutover_at <= completed_at,
            "completed_at must not be earlier than planned_cutover_at",
        )

        duration = (completed_at - prepared_at).total_seconds()

        require(
            duration
            <= document["handoff_window"]["maximum_duration_seconds"],
            "handoff duration exceeds maximum_duration_seconds",
        )

    released_value = authority["released_at"]
    acquired_value = authority["acquired_at"]

    if released_value is not None and acquired_value is not None:
        released_at = parse_datetime(
            released_value,
            "authority_transfer.released_at",
        )
        acquired_at = parse_datetime(
            acquired_value,
            "authority_transfer.acquired_at",
        )

        require(
            released_at <= acquired_at,
            "authority must be released before or at acquisition",
        )

    if document["handoff_phase"] == "COMPLETED":
        require(
            authority["status"] == "COMPLETE",
            "completed handoff requires COMPLETE authority transfer",
        )
        require(
            verification["required_checks_passed"] is True,
            "completed handoff requires mandatory verification",
        )
        require(
            not verification["blocking_issues"],
            "completed handoff cannot contain verification blockers",
        )
        require(
            acceptance["status"] == "ACCEPTED",
            "completed handoff requires explicit acceptance",
        )
        require(
            continuity_guard["service_status"] != "INTERRUPTED",
            "interrupted handoff cannot be marked COMPLETED",
        )
        require(
            continuity_guard["duplicate_execution_detected"] is False,
            "completed handoff cannot contain duplicate execution",
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


def validate_rotation_policy_semantics(
    document: dict[str, Any],
    context: dict[str, Any],
) -> None:
    """Validate adaptive rotation policy invariants."""

    del context

    signals = document["signals"]
    signal_ids = [signal["signal_id"] for signal in signals]

    require(
        len(signal_ids) == len(set(signal_ids)),
        "signal_id values must be unique",
    )

    total_weight = sum(float(signal["weight"]) for signal in signals)

    require(
        approximately_equal(total_weight, 1.0),
        f"signal weights must sum to 1.0, got {total_weight}",
    )

    for signal in signals:
        warning = signal["warning_threshold"]
        critical = signal["critical_threshold"]
        direction = signal["direction"]

        if direction == "HIGHER_IS_WORSE":
            require(
                warning < critical,
                f"{signal['signal_id']} warning threshold "
                "must be lower than critical threshold",
            )
        else:
            require(
                warning > critical,
                f"{signal['signal_id']} warning threshold "
                "must be higher than critical threshold",
            )

    scoring = document["scoring"]

    require(
        scoring["warning_score"] < scoring["rotation_score"],
        "warning_score must be lower than rotation_score",
    )

    guards = document["guards"]

    require(
        guards["minimum_active_duration_seconds"]
        < guards["maximum_active_duration_seconds"],
        "minimum active duration must be lower than maximum duration",
    )

    hard_trigger_ids = [
        trigger["trigger_id"]
        for trigger in document["hard_triggers"]
    ]

    require(
        len(hard_trigger_ids) == len(set(hard_trigger_ids)),
        "hard trigger IDs must be unique",
    )

    known_signal_ids = set(signal_ids)

    for trigger in document["hard_triggers"]:
        require(
            trigger["signal_id"] in known_signal_ids,
            f"hard trigger {trigger['trigger_id']} "
            "references an unknown signal",
        )


def determine_threshold_state(
    raw_value: float,
    direction: str,
    warning: float,
    critical: float,
) -> str:
    """Determine the expected threshold classification."""

    if direction == "HIGHER_IS_WORSE":
        if raw_value >= critical:
            return "CRITICAL"
        if raw_value >= warning:
            return "WARNING"
        return "NORMAL"

    if raw_value <= critical:
        return "CRITICAL"
    if raw_value <= warning:
        return "WARNING"

    return "NORMAL"


def trigger_is_active(
    raw_value: float,
    operator: str,
    threshold: float,
) -> bool:
    """Evaluate one hard-trigger comparison."""

    if operator == "GT":
        return raw_value > threshold
    if operator == "GTE":
        return raw_value >= threshold
    if operator == "LT":
        return raw_value < threshold
    if operator == "LTE":
        return raw_value <= threshold

    raise SemanticValidationError(
        f"unsupported hard-trigger operator: {operator}"
    )


def validate_rotation_evaluation_semantics(
    document: dict[str, Any],
    context: dict[str, Any],
) -> None:
    """Validate adaptive rotation evaluation and decision invariants."""

    policy_id = document["policy_id"]
    policies = context["policies"]

    require(
        policy_id in policies,
        f"rotation policy not found for policy_id: {policy_id}",
    )

    policy = policies[policy_id]

    require(
        document["system_id"] == policy["system_id"],
        "evaluation system_id must match policy system_id",
    )

    active_unit_id = document["active_unit"]["unit_id"]
    assuming = document["candidate_units"]["assuming_candidate"]
    continuity = document["candidate_units"]["continuity_candidate"]

    require(
        len(
            {
                active_unit_id,
                assuming["unit_id"],
                continuity["unit_id"],
            }
        )
        == 3,
        "active, assuming, and continuity units must be distinct",
    )

    policy_signals = {
        signal["signal_id"]: signal
        for signal in policy["signals"]
    }

    observations = document["signal_observations"]
    observed_ids = [
        observation["signal_id"]
        for observation in observations
    ]

    require(
        len(observed_ids) == len(set(observed_ids)),
        "signal observations must use unique signal IDs",
    )

    required_ids = {
        signal["signal_id"]
        for signal in policy["signals"]
        if signal["required"]
    }

    require(
        required_ids.issubset(set(observed_ids)),
        "evaluation is missing one or more required signals",
    )

    computed_total = 0.0
    raw_values: dict[str, float] = {}

    for observation in observations:
        signal_id = observation["signal_id"]

        require(
            signal_id in policy_signals,
            f"unknown observed signal: {signal_id}",
        )

        rule = policy_signals[signal_id]

        require(
            observation["direction"] == rule["direction"],
            f"{signal_id} direction does not match policy",
        )
        require(
            approximately_equal(
                observation["weight_used"],
                rule["weight"],
            ),
            f"{signal_id} weight does not match policy",
        )
        require(
            approximately_equal(
                observation["warning_threshold_used"],
                rule["warning_threshold"],
            ),
            f"{signal_id} warning threshold does not match policy",
        )
        require(
            approximately_equal(
                observation["critical_threshold_used"],
                rule["critical_threshold"],
            ),
            f"{signal_id} critical threshold does not match policy",
        )

        expected_contribution = (
            observation["normalized_value"]
            * observation["weight_used"]
        )

        require(
            approximately_equal(
                observation["contribution"],
                expected_contribution,
            ),
            f"{signal_id} contribution is incorrect",
        )

        expected_state = determine_threshold_state(
            raw_value=observation["raw_value"],
            direction=observation["direction"],
            warning=observation["warning_threshold_used"],
            critical=observation["critical_threshold_used"],
        )

        require(
            observation["threshold_state"] == expected_state,
            f"{signal_id} threshold_state should be {expected_state}",
        )

        computed_total += observation["contribution"]
        raw_values[signal_id] = observation["raw_value"]

    score = document["score"]

    require(
        approximately_equal(score["total_score"], computed_total),
        f"total_score should be {computed_total}",
    )
    require(
        approximately_equal(
            score["warning_score"],
            policy["scoring"]["warning_score"],
        ),
        "warning_score does not match policy",
    )
    require(
        approximately_equal(
            score["rotation_score"],
            policy["scoring"]["rotation_score"],
        ),
        "rotation_score does not match policy",
    )
    require(
        score["required_consecutive_breaches"]
        == policy["scoring"]["required_consecutive_breaches"],
        "required_consecutive_breaches does not match policy",
    )

    triggered_ids: list[str] = []

    for trigger in policy["hard_triggers"]:
        signal_id = trigger["signal_id"]

        if signal_id not in raw_values:
            continue

        if trigger_is_active(
            raw_value=raw_values[signal_id],
            operator=trigger["operator"],
            threshold=trigger["threshold"],
        ):
            triggered_ids.append(trigger["trigger_id"])

    require(
        score["hard_triggered"] == bool(triggered_ids),
        "hard_triggered does not match evaluated trigger state",
    )
    require(
        set(score["hard_trigger_ids"]) == set(triggered_ids),
        "hard_trigger_ids do not match active hard triggers",
    )

    guards = document["guard_evaluation"]
    policy_guards = policy["guards"]
    active = document["active_unit"]

    require(
        guards["minimum_active_duration_seconds"]
        == policy_guards["minimum_active_duration_seconds"],
        "minimum active duration does not match policy",
    )
    require(
        guards["maximum_active_duration_seconds"]
        == policy_guards["maximum_active_duration_seconds"],
        "maximum active duration does not match policy",
    )
    require(
        approximately_equal(
            guards["minimum_shadow_readiness_score"],
            policy_guards["minimum_shadow_readiness_score"],
        ),
        "shadow readiness threshold does not match policy",
    )
    require(
        approximately_equal(
            guards["minimum_regeneration_completion_score"],
            policy_guards[
                "minimum_regeneration_completion_score"
            ],
        ),
        "regeneration threshold does not match policy",
    )
    require(
        guards["cooldown_seconds"]
        == policy_guards["cooldown_seconds"],
        "cooldown does not match policy",
    )

    expected_active_satisfied = (
        active["active_duration_seconds"]
        >= guards["minimum_active_duration_seconds"]
    )
    expected_maximum_reached = (
        active["active_duration_seconds"]
        >= guards["maximum_active_duration_seconds"]
    )
    expected_shadow_ready = (
        assuming["readiness_score"]
        >= guards["minimum_shadow_readiness_score"]
    )
    expected_regeneration_ready = (
        continuity["readiness_score"]
        >= guards["minimum_regeneration_completion_score"]
    )
    expected_cooldown = (
        guards["cooldown_elapsed_seconds"]
        >= guards["cooldown_seconds"]
    )

    require(
        guards["active_duration_satisfied"]
        == expected_active_satisfied,
        "active_duration_satisfied is incorrect",
    )
    require(
        guards["maximum_duration_reached"]
        == expected_maximum_reached,
        "maximum_duration_reached is incorrect",
    )
    require(
        guards["shadow_readiness_satisfied"]
        == expected_shadow_ready,
        "shadow_readiness_satisfied is incorrect",
    )
    require(
        guards["regeneration_completion_satisfied"]
        == expected_regeneration_ready,
        "regeneration_completion_satisfied is incorrect",
    )
    require(
        guards["cooldown_satisfied"] == expected_cooldown,
        "cooldown_satisfied is incorrect",
    )

    blockers_absent = not guards["handoff_blockers"]

    expected_guards_passed = (
        expected_active_satisfied
        and expected_shadow_ready
        and expected_regeneration_ready
        and expected_cooldown
        and (
            blockers_absent
            or policy_guards["allow_rotation_with_blockers"]
        )
    )

    if guards["emergency_override"]:
        expected_guards_passed = (
            expected_shadow_ready
            and expected_regeneration_ready
        )

    require(
        guards["all_required_guards_passed"]
        == expected_guards_passed,
        "all_required_guards_passed is inconsistent",
    )

    decision = document["decision"]

    if decision["action"] in {
        "ROTATE_NOW",
        "ROTATE_AT",
        "EMERGENCY_REASSIGN",
    }:
        require(
            decision["selected_assuming_unit_id"]
            == assuming["unit_id"],
            "selected assuming unit is incorrect",
        )
        require(
            decision["selected_continuity_unit_id"]
            == continuity["unit_id"],
            "selected continuity unit is incorrect",
        )
        require(
            decision["planned_handoff_id"] is not None,
            "rotation decision requires planned_handoff_id",
        )

    threshold_reached = (
        score["total_score"] >= score["rotation_score"]
        and score["consecutive_threshold_breaches"]
        >= score["required_consecutive_breaches"]
    )

    rotation_required = (
        threshold_reached
        or guards["maximum_duration_reached"]
        or score["hard_triggered"]
    )

    if rotation_required and guards["all_required_guards_passed"]:
        require(
            decision["action"]
            in {
                "ROTATE_NOW",
                "ROTATE_AT",
                "EMERGENCY_REASSIGN",
                "ABORT_ACTIVE_WORK",
            },
            "rotation conditions were met but decision action does not rotate",
        )

    if (
        decision["action"] == "HOLD"
        and rotation_required
        and guards["all_required_guards_passed"]
    ):
        raise SemanticValidationError(
            "HOLD is invalid when rotation is required and guards pass"
        )


SemanticValidator = Callable[
    [dict[str, Any], dict[str, Any]],
    None,
]

SEMANTIC_VALIDATORS: dict[str, SemanticValidator] = {
    "validate_shift_handoff_semantics":
        validate_shift_handoff_semantics,
    "validate_rotation_policy_semantics":
        validate_rotation_policy_semantics,
    "validate_rotation_evaluation_semantics":
        validate_rotation_evaluation_semantics,
}


def validate_schema(
    name: str,
    schema_path: Path,
    example_path: Path,
) -> tuple[bool, dict[str, Any] | None]:
    """Validate one example against its JSON Schema."""

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

        return False, example

    print("[schema-ok]")
    return True, example


def build_context(
    loaded_documents: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build cross-document validation context."""

    policies: dict[str, dict[str, Any]] = {}

    for document in loaded_documents:
        if document.get("record_type") == "adaptive_rotation_policy":
            policies[document["policy_id"]] = document

    return {
        "policies": policies,
    }


def main() -> int:
    """Validate all protocol examples."""

    print("=== Tri-Shift AI Rotation Protocol Validation ===")
    print()

    loaded: list[tuple[dict[str, Any], dict[str, Any]]] = []
    loaded_documents: list[dict[str, Any]] = []
    all_valid = True

def validate_multi_wing_matrix_semantics(
    document: dict[str, Any],
    context: dict[str, Any],
) -> None:
    """Validate Multi-Wing Shift Matrix invariants."""

    del context

    wing_definitions = document["wing_definitions"]
    rotation_domains = document["rotation_domains"]
    assignments = document["assignments"]
    dependencies = document["dependencies"]
    constraints = document["constraints"]
    matrix_health = document["matrix_health"]

    wing_map = {
        wing["wing_id"]: wing
        for wing in wing_definitions
    }

    require(
        len(wing_map) == len(wing_definitions),
        "wing_definition wing_id values must be unique",
    )

    domain_map = {
        domain["domain_id"]: domain
        for domain in rotation_domains
    }

    require(
        len(domain_map) == len(rotation_domains),
        "rotation domain IDs must be unique",
    )

    assignment_ids = [
        assignment["assignment_id"]
        for assignment in assignments
    ]

    require(
        len(assignment_ids) == len(set(assignment_ids)),
        "assignment_id values must be unique",
    )

    assigned_wing_ids = [
        assignment["wing_id"]
        for assignment in assignments
    ]

    require(
        len(assigned_wing_ids) == len(set(assigned_wing_ids)),
        "each wing must have exactly one matrix assignment",
    )

    require(
        set(assigned_wing_ids) == set(wing_map),
        "every declared wing must have exactly one assignment",
    )

    wing_domain_map: dict[str, str] = {}

    for domain in rotation_domains:
        group_ids = {
            domain["active_group_id"],
            domain["shadow_group_id"],
            domain["regeneration_group_id"],
        }

        require(
            len(group_ids) == 3,
            f"rotation domain {domain['domain_id']} "
            "must use three distinct groups",
        )

        for wing_id in domain["wing_ids"]:
            require(
                wing_id in wing_map,
                f"domain {domain['domain_id']} references "
                f"unknown wing {wing_id}",
            )

            require(
                wing_id not in wing_domain_map,
                f"wing {wing_id} belongs to multiple rotation domains",
            )

            wing_domain_map[wing_id] = domain["domain_id"]

    require(
        set(wing_domain_map) == set(wing_map),
        "every wing must belong to exactly one rotation domain",
    )

    assignment_map = {
        assignment["wing_id"]: assignment
        for assignment in assignments
    }

    for domain_id, domain in domain_map.items():
        expected_wings = set(domain["wing_ids"])

        actual_wings = {
            assignment["wing_id"]
            for assignment in assignments
            if assignment["domain_id"] == domain_id
        }

        require(
            expected_wings == actual_wings,
            f"domain {domain_id} wing list does not match assignments",
        )

    critical_fully_covered = 0

    for assignment in assignments:
        wing_id = assignment["wing_id"]
        domain_id = assignment["domain_id"]

        require(
            wing_id in wing_map,
            f"assignment references unknown wing {wing_id}",
        )
        require(
            domain_id in domain_map,
            f"assignment references unknown domain {domain_id}",
        )
        require(
            wing_domain_map[wing_id] == domain_id,
            f"wing {wing_id} is assigned to the wrong domain",
        )

        wing = wing_map[wing_id]
        domain = domain_map[domain_id]

        active = assignment["active_slot"]
        shadow = assignment["shadow_slot"]
        regeneration = assignment["regeneration_slot"]

        require(
            active["group_id"] == domain["active_group_id"],
            f"{wing_id} active slot has the wrong group_id",
        )
        require(
            shadow["group_id"] == domain["shadow_group_id"],
            f"{wing_id} shadow slot has the wrong group_id",
        )
        require(
            regeneration["group_id"]
            == domain["regeneration_group_id"],
            f"{wing_id} regeneration slot has the wrong group_id",
        )

        member_ids = {
            active["member_id"],
            shadow["member_id"],
            regeneration["member_id"],
        }

        if not constraints["allow_same_member_across_states"]:
            require(
                len(member_ids) == 3,
                f"{wing_id} must use distinct members "
                "across all three shift states",
            )

        required_capabilities = set(
            wing["required_capabilities"]
        )

        for slot_name, slot in [
            ("active", active),
            ("shadow", shadow),
            ("regeneration", regeneration),
        ]:
            slot_capabilities = set(slot["capabilities"])

            require(
                required_capabilities.issubset(
                    slot_capabilities
                ),
                f"{wing_id} {slot_name} slot is missing "
                "required capabilities",
            )

        require(
            shadow["takeover_readiness_score"]
            >= constraints[
                "minimum_shadow_takeover_readiness_score"
            ],
            f"{wing_id} shadow takeover readiness is too low",
        )

        require(
            shadow["synchronization_score"]
            >= constraints[
                "minimum_shadow_synchronization_score"
            ],
            f"{wing_id} shadow synchronization is too low",
        )

        require(
            regeneration["regeneration_completion_score"]
            >= constraints[
                "minimum_regeneration_completion_score"
            ],
            f"{wing_id} regeneration completion is too low",
        )

        if wing["criticality"] == "CRITICAL":
            if constraints[
                "provider_diversity_required_for_critical_wings"
            ]:
                providers = {
                    active["provider"],
                    shadow["provider"],
                    regeneration["provider"],
                }

                require(
                    None not in providers and len(providers) == 3,
                    f"critical wing {wing_id} must use "
                    "three distinct providers",
                )

            if constraints[
                "region_diversity_required_for_critical_wings"
            ]:
                regions = {
                    active["region"],
                    shadow["region"],
                    regeneration["region"],
                }

                require(
                    None not in regions and len(regions) == 3,
                    f"critical wing {wing_id} must use "
                    "three distinct regions",
                )

            fully_covered = all(
                slot["health_state"] != "BLOCKED"
                for slot in [
                    active,
                    shadow,
                    regeneration,
                ]
            )

            if fully_covered:
                critical_fully_covered += 1

    dependency_ids = [
        dependency["dependency_id"]
        for dependency in dependencies
    ]

    require(
        len(dependency_ids) == len(set(dependency_ids)),
        "dependency_id values must be unique",
    )

    for dependency in dependencies:
        source = dependency["source_wing_id"]
        target = dependency["target_wing_id"]

        require(
            source in wing_map,
            f"dependency references unknown source wing {source}",
        )
        require(
            target in wing_map,
            f"dependency references unknown target wing {target}",
        )
        require(
            source != target,
            f"dependency {dependency['dependency_id']} "
            "cannot reference the same wing twice",
        )

        source_domain = wing_domain_map[source]
        target_domain = wing_domain_map[target]

        if not constraints["allow_cross_domain_dependencies"]:
            require(
                source_domain == target_domain,
                f"cross-domain dependency "
                f"{dependency['dependency_id']} is not allowed",
            )

    total_wings = len(wing_definitions)
    assigned_wings = len(assignments)

    critical_wings = sum(
        1
        for wing in wing_definitions
        if wing["criticality"] == "CRITICAL"
    )

    coverage_ratio = (
        assigned_wings / total_wings
        if total_wings
        else 0.0
    )

    critical_coverage_ratio = (
        critical_fully_covered / critical_wings
        if critical_wings
        else 1.0
    )

    require(
        matrix_health["total_wings"] == total_wings,
        "matrix_health.total_wings is incorrect",
    )
    require(
        matrix_health["assigned_wings"] == assigned_wings,
        "matrix_health.assigned_wings is incorrect",
    )
    require(
        matrix_health["critical_wings"] == critical_wings,
        "matrix_health.critical_wings is incorrect",
    )
    require(
        matrix_health["critical_wings_fully_covered"]
        == critical_fully_covered,
        "critical_wings_fully_covered is incorrect",
    )
    require(
        approximately_equal(
            matrix_health["coverage_ratio"],
            coverage_ratio,
        ),
        "matrix_health.coverage_ratio is incorrect",
    )
    require(
        approximately_equal(
            matrix_health["critical_coverage_ratio"],
            critical_coverage_ratio,
        ),
        "matrix_health.critical_coverage_ratio is incorrect",
    )

    all_active_healthy = all(
        assignment["active_slot"]["health_state"]
        != "BLOCKED"
        for assignment in assignments
    )

    expected_rotation_ready = (
        not matrix_health["blocking_conflicts"]
        and all_active_healthy
        and coverage_ratio == 1.0
        and critical_coverage_ratio
        >= constraints["minimum_critical_coverage_ratio"]
    )

    require(
        matrix_health["rotation_ready"]
        == expected_rotation_ready,
        "matrix_health.rotation_ready is inconsistent",
    )

{
    "name": "Continuous Operation Receipt",
    "schema": (
        ROOT_DIR
        / "schemas"
        / "continuous-operation-receipt.schema.json"
    ),
    "example": (
        ROOT_DIR
        / "examples"
        / "continuous-operation-receipt.example.yaml"
    ),
    "semantic_validator":
        "validate_continuous_operation_receipt_semantics",
},
    
    try:
        for target in VALIDATION_TARGETS:
            schema_valid, document = validate_schema(
                name=target["name"],
                schema_path=target["schema"],
                example_path=target["example"],
            )

            if document is not None:
                loaded_documents.append(document)
                loaded.append((target, document))

            all_valid = all_valid and schema_valid
            print()

        if not all_valid:
            print("Schema validation failed.")
            return 1

        context = build_context(loaded_documents)

        for target, document in loaded:
            validator_name = target["semantic_validator"]

            if validator_name is None:
                continue

            print(f"[semantic] {target['name']}")

            semantic_validator = SEMANTIC_VALIDATORS[
                validator_name
            ]

            try:
                semantic_validator(document, context)
            except SemanticValidationError as exc:
                print(f"[semantic-error] {exc}")
                all_valid = False
            else:
                print("[semantic-ok]")

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
