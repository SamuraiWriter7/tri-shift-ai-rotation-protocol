#!/usr/bin/env python3
"""Validate Tri-Shift AI Rotation Protocol examples.

Validation is performed in two stages:

1. JSON Schema validation
2. Protocol-level semantic validation

The semantic stage checks cross-field and cross-document invariants that are
difficult or impossible to express with JSON Schema alone.
"""

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


VALIDATION_TARGETS: list[dict[str, Any]] = [
    {
        "name": "Shift State Record",
        "schema": (
            ROOT_DIR
            / "schemas"
            / "shift-state-record.schema.json"
        ),
        "example": (
            ROOT_DIR
            / "examples"
            / "shift-state-record.example.yaml"
        ),
        "semantic_validator": "validate_shift_state_semantics",
    },
    {
        "name": "Shift Handoff Record",
        "schema": (
            ROOT_DIR
            / "schemas"
            / "shift-handoff-record.schema.json"
        ),
        "example": (
            ROOT_DIR
            / "examples"
            / "shift-handoff-record.example.yaml"
        ),
        "semantic_validator": "validate_shift_handoff_semantics",
    },
    {
        "name": "Adaptive Rotation Policy",
        "schema": (
            ROOT_DIR
            / "schemas"
            / "adaptive-rotation-policy.schema.json"
        ),
        "example": (
            ROOT_DIR
            / "examples"
            / "adaptive-rotation-policy.example.yaml"
        ),
        "semantic_validator": "validate_rotation_policy_semantics",
    },
    {
        "name": "Rotation Evaluation Record",
        "schema": (
            ROOT_DIR
            / "schemas"
            / "rotation-evaluation-record.schema.json"
        ),
        "example": (
            ROOT_DIR
            / "examples"
            / "rotation-evaluation-record.example.yaml"
        ),
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
        "semantic_validator": (
            "validate_continuous_operation_receipt_semantics"
        ),
    },
]


class SemanticValidationError(ValueError):
    """Raised when a document violates protocol-level invariants."""


SemanticValidator = Callable[
    [dict[str, Any], dict[str, Any]],
    None,
]


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    try:
        with path.open("r", encoding="utf-8") as file:
            document = json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in {path}: "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(f"Unable to read JSON file {path}: {exc}") from exc

    if not isinstance(document, dict):
        raise RuntimeError(f"Expected a JSON object in {path}")

    return document


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping from disk."""

    try:
        with path.open("r", encoding="utf-8") as file:
            document = yaml.safe_load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"YAML file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Invalid YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"Unable to read YAML file {path}: {exc}") from exc

    if not isinstance(document, dict):
        raise RuntimeError(f"Expected a YAML mapping in {path}")

    return document


def parse_datetime(value: Any, field_name: str) -> datetime:
    """Parse an ISO-8601 or RFC3339-compatible date-time value."""

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise SemanticValidationError(
            f"{field_name} must be a date-time string"
        )

    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SemanticValidationError(
            f"{field_name} must be a valid date-time: {value}"
        ) from exc


def require(condition: bool, message: str) -> None:
    """Raise a semantic error when a required condition is false."""

    if not condition:
        raise SemanticValidationError(message)


def approximately_equal(
    left: float,
    right: float,
    *,
    tolerance: float = 1e-6,
) -> bool:
    """Compare two floating-point values with a small tolerance."""

    return math.isclose(
        float(left),
        float(right),
        rel_tol=tolerance,
        abs_tol=tolerance,
    )


def format_error_path(error: Any) -> str:
    """Convert a jsonschema error path into readable dotted notation."""

    if not error.absolute_path:
        return "<root>"

    parts: list[str] = []

    for component in error.absolute_path:
        if isinstance(component, int):
            parts.append(f"[{component}]")
        elif not parts:
            parts.append(str(component))
        else:
            parts.append(f".{component}")

    return "".join(parts)


def require_unique(
    values: list[str],
    field_name: str,
) -> None:
    """Require all values in a list to be unique."""

    require(
        len(values) == len(set(values)),
        f"{field_name} values must be unique",
    )


def reference_tail(reference: str) -> str:
    """Return the final identifier component of a protocol reference."""

    value = reference.rstrip("/")
    return value.rsplit("/", maxsplit=1)[-1]


def determine_threshold_state(
    *,
    raw_value: float,
    direction: str,
    warning: float,
    critical: float,
) -> str:
    """Determine the expected threshold state for one signal."""

    if direction == "HIGHER_IS_WORSE":
        if raw_value >= critical:
            return "CRITICAL"
        if raw_value >= warning:
            return "WARNING"
        return "NORMAL"

    if direction == "LOWER_IS_WORSE":
        if raw_value <= critical:
            return "CRITICAL"
        if raw_value <= warning:
            return "WARNING"
        return "NORMAL"

    raise SemanticValidationError(
        f"Unsupported signal direction: {direction}"
    )


def trigger_is_active(
    *,
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
        f"Unsupported hard-trigger operator: {operator}"
    )


def validate_shift_state_semantics(
    document: dict[str, Any],
    context: dict[str, Any],
) -> None:
    """Validate Shift State Record semantic invariants."""

    del context

    state_window = document["state_window"]
    started_at = parse_datetime(
        state_window["started_at"],
        "state_window.started_at",
    )
    planned_end_at = parse_datetime(
        state_window["planned_end_at"],
        "state_window.planned_end_at",
    )

    require(
        started_at < planned_end_at,
        "state_window.started_at must be earlier than planned_end_at",
    )

    actual_end_value = state_window.get("actual_end_at")

    if actual_end_value is not None:
        actual_end_at = parse_datetime(
            actual_end_value,
            "state_window.actual_end_at",
        )

        require(
            actual_end_at >= started_at,
            "state_window.actual_end_at cannot precede started_at",
        )

    planned_duration = int(
        (planned_end_at - started_at).total_seconds()
    )

    maximum_duration = document["rotation_policy"][
        "maximum_shift_duration_seconds"
    ]

    require(
        planned_duration <= maximum_duration,
        "planned shift duration exceeds "
        "rotation_policy.maximum_shift_duration_seconds",
    )

    handoff = document["handoff"]

    if handoff["readiness"] == "BLOCKED":
        require(
            bool(handoff["blockers"]),
            "handoff readiness BLOCKED requires at least one blocker",
        )

    if handoff["readiness"] == "READY":
        require(
            not handoff["blockers"],
            "handoff readiness READY cannot contain blockers",
        )

    unit_ids = [
        member["member_id"]
        for member in document["shift_unit"]["members"]
    ]

    require_unique(
        unit_ids,
        "shift_unit.members.member_id",
    )


def validate_shift_handoff_semantics(
    document: dict[str, Any],
    context: dict[str, Any],
) -> None:
    """Validate tri-party Shift Handoff Record invariants."""

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
        "authority_transfer.previous_holder must match "
        "the releasing unit",
    )
    require(
        authority["next_holder"] == assuming,
        "authority_transfer.next_holder must match "
        "the assuming unit",
    )
    require(
        authority["rollback_target_unit_id"] == releasing,
        "authority_transfer.rollback_target_unit_id must match "
        "the releasing unit",
    )
    require(
        authority["dual_primary_allowed"] is False,
        "dual primary authority must not be allowed",
    )

    verification = document["verification"]
    acceptance = document["acceptance"]
    continuity_guard = document["continuity_guard"]

    require(
        verification["verifier_unit_id"] == continuity,
        "verification.verifier_unit_id must match "
        "the continuity unit",
    )
    require(
        continuity_guard["guarded_by_unit_id"] == continuity,
        "continuity_guard.guarded_by_unit_id must match "
        "the continuity unit",
    )

    if acceptance["status"] in {"ACCEPTED", "CONDITIONAL"}:
        require(
            acceptance["accepted_by_unit_id"] == assuming,
            "acceptance.accepted_by_unit_id must match "
            "the assuming unit",
        )

    active_tasks = document["transfer_payload"]["active_tasks"]

    task_ids = [task["task_id"] for task in active_tasks]
    require_unique(task_ids, "transfer_payload.active_tasks.task_id")

    for task in active_tasks:
        require(
            task["owner_before"] == releasing,
            f"task {task['task_id']} owner_before must match "
            "the releasing unit",
        )
        require(
            task["owner_after"] == assuming,
            f"task {task['task_id']} owner_after must match "
            "the assuming unit",
        )

    risk_flags = document["transfer_payload"]["risk_flags"]
    risk_ids = [risk["risk_id"] for risk in risk_flags]
    require_unique(risk_ids, "transfer_payload.risk_flags.risk_id")

    decision_ids = [
        decision["decision_id"]
        for decision in document["transfer_payload"][
            "unresolved_decisions"
        ]
    ]
    require_unique(
        decision_ids,
        "transfer_payload.unresolved_decisions.decision_id",
    )

    checks = verification["checks"]
    check_ids = [check["check_id"] for check in checks]
    require_unique(check_ids, "verification.checks.check_id")

    prepared_at = parse_datetime(
        document["handoff_window"]["prepared_at"],
        "handoff_window.prepared_at",
    )
    planned_cutover_at = parse_datetime(
        document["handoff_window"]["planned_cutover_at"],
        "handoff_window.planned_cutover_at",
    )

    require(
        prepared_at <= planned_cutover_at,
        "handoff_window.prepared_at must not be later than "
        "planned_cutover_at",
    )

    completed_at_value = document["handoff_window"]["completed_at"]

    if completed_at_value is not None:
        completed_at = parse_datetime(
            completed_at_value,
            "handoff_window.completed_at",
        )

        require(
            completed_at >= planned_cutover_at,
            "handoff_window.completed_at must not precede "
            "planned_cutover_at",
        )

        handoff_duration = (
            completed_at - prepared_at
        ).total_seconds()

        require(
            handoff_duration
            <= document["handoff_window"][
                "maximum_duration_seconds"
            ],
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
            "primary authority must be released before or at "
            "the moment it is acquired",
        )

    if document["handoff_phase"] == "COMPLETED":
        require(
            authority["status"] == "COMPLETE",
            "a completed handoff requires authority status COMPLETE",
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
            "a completed handoff requires acceptance.accepted_at",
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
            for task in active_tasks
            if task["blocking"]
        ]

        blocking_risks = [
            risk["risk_id"]
            for risk in risk_flags
            if risk["blocking"]
        ]

        require(
            not blocking_tasks,
            f"completed handoff contains blocking tasks: "
            f"{blocking_tasks}",
        )
        require(
            not blocking_risks,
            f"completed handoff contains blocking risks: "
            f"{blocking_risks}",
        )


def validate_rotation_policy_semantics(
    document: dict[str, Any],
    context: dict[str, Any],
) -> None:
    """Validate Adaptive Rotation Policy invariants."""

    del context

    signals = document["signals"]
    signal_ids = [signal["signal_id"] for signal in signals]

    require_unique(signal_ids, "signals.signal_id")

    total_weight = sum(
        float(signal["weight"])
        for signal in signals
    )

    require(
        approximately_equal(total_weight, 1.0),
        f"signal weights must sum to 1.0; got {total_weight}",
    )

    for signal in signals:
        warning = float(signal["warning_threshold"])
        critical = float(signal["critical_threshold"])
        direction = signal["direction"]

        if direction == "HIGHER_IS_WORSE":
            require(
                warning < critical,
                f"{signal['signal_id']}: warning threshold must be "
                "lower than critical threshold",
            )
        elif direction == "LOWER_IS_WORSE":
            require(
                warning > critical,
                f"{signal['signal_id']}: warning threshold must be "
                "higher than critical threshold",
            )

    scoring = document["scoring"]

    require(
        scoring["warning_score"] < scoring["rotation_score"],
        "scoring.warning_score must be lower than rotation_score",
    )

    guards = document["guards"]

    require(
        guards["minimum_active_duration_seconds"]
        < guards["maximum_active_duration_seconds"],
        "minimum active duration must be lower than "
        "maximum active duration",
    )

    require(
        document["evaluation_cadence"]["rolling_window_seconds"]
        >= document["evaluation_cadence"]["interval_seconds"],
        "rolling window must not be shorter than "
        "the evaluation interval",
    )

    hard_triggers = document["hard_triggers"]
    hard_trigger_ids = [
        trigger["trigger_id"]
        for trigger in hard_triggers
    ]

    require_unique(
        hard_trigger_ids,
        "hard_triggers.trigger_id",
    )

    known_signal_ids = set(signal_ids)

    for trigger in hard_triggers:
        require(
            trigger["signal_id"] in known_signal_ids,
            f"hard trigger {trigger['trigger_id']} references "
            f"unknown signal {trigger['signal_id']}",
        )

    fairness = document["fairness"]

    require(
        fairness["maximum_active_share"] >= (1 / 3),
        "fairness.maximum_active_share cannot be lower than "
        "the ideal share of a three-unit rotation",
    )


def validate_rotation_evaluation_semantics(
    document: dict[str, Any],
    context: dict[str, Any],
) -> None:
    """Validate Rotation Evaluation Record invariants."""

    policy_id = document["policy_id"]
    policies = context["policies"]

    require(
        policy_id in policies,
        f"adaptive rotation policy not found: {policy_id}",
    )

    policy = policies[policy_id]

    require(
        document["system_id"] == policy["system_id"],
        "evaluation system_id must match policy system_id",
    )

    active = document["active_unit"]
    assuming = document["candidate_units"]["assuming_candidate"]
    continuity = document["candidate_units"]["continuity_candidate"]

    require(
        len(
            {
                active["unit_id"],
                assuming["unit_id"],
                continuity["unit_id"],
            }
        )
        == 3,
        "active, assuming, and continuity units must be distinct",
    )

    window = document["evaluation_window"]
    window_started = parse_datetime(
        window["started_at"],
        "evaluation_window.started_at",
    )
    window_ended = parse_datetime(
        window["ended_at"],
        "evaluation_window.ended_at",
    )

    require(
        window_started < window_ended,
        "evaluation window start must precede its end",
    )

    evaluation_duration = int(
        (window_ended - window_started).total_seconds()
    )

    cadence = policy["evaluation_cadence"]

    require(
        window["sample_count"] >= cadence["minimum_samples"],
        "evaluation sample_count is below policy minimum_samples",
    )
    require(
        evaluation_duration <= cadence["rolling_window_seconds"],
        "evaluation window exceeds policy rolling_window_seconds",
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

    require_unique(
        observed_ids,
        "signal_observations.signal_id",
    )

    required_signal_ids = {
        signal["signal_id"]
        for signal in policy["signals"]
        if signal["required"]
    }

    require(
        required_signal_ids.issubset(set(observed_ids)),
        "evaluation is missing one or more required signals",
    )

    computed_total = 0.0
    raw_values: dict[str, float] = {}

    for observation in observations:
        signal_id = observation["signal_id"]

        require(
            signal_id in policy_signals,
            f"evaluation contains unknown signal: {signal_id}",
        )

        rule = policy_signals[signal_id]

        require(
            observation["direction"] == rule["direction"],
            f"{signal_id}: direction does not match policy",
        )
        require(
            approximately_equal(
                observation["weight_used"],
                rule["weight"],
            ),
            f"{signal_id}: weight_used does not match policy",
        )
        require(
            approximately_equal(
                observation["warning_threshold_used"],
                rule["warning_threshold"],
            ),
            f"{signal_id}: warning threshold does not match policy",
        )
        require(
            approximately_equal(
                observation["critical_threshold_used"],
                rule["critical_threshold"],
            ),
            f"{signal_id}: critical threshold does not match policy",
        )

        expected_contribution = (
            float(observation["normalized_value"])
            * float(observation["weight_used"])
        )

        require(
            approximately_equal(
                observation["contribution"],
                expected_contribution,
            ),
            f"{signal_id}: contribution should be "
            f"{expected_contribution}",
        )

        expected_threshold_state = determine_threshold_state(
            raw_value=float(observation["raw_value"]),
            direction=observation["direction"],
            warning=float(
                observation["warning_threshold_used"]
            ),
            critical=float(
                observation["critical_threshold_used"]
            ),
        )

        require(
            observation["threshold_state"]
            == expected_threshold_state,
            f"{signal_id}: threshold_state should be "
            f"{expected_threshold_state}",
        )

        computed_total += expected_contribution
        raw_values[signal_id] = float(
            observation["raw_value"]
        )

    score = document["score"]

    require(
        approximately_equal(
            score["total_score"],
            computed_total,
        ),
        f"score.total_score should be {computed_total}",
    )
    require(
        approximately_equal(
            score["warning_score"],
            policy["scoring"]["warning_score"],
        ),
        "score.warning_score does not match policy",
    )
    require(
        approximately_equal(
            score["rotation_score"],
            policy["scoring"]["rotation_score"],
        ),
        "score.rotation_score does not match policy",
    )
    require(
        score["required_consecutive_breaches"]
        == policy["scoring"][
            "required_consecutive_breaches"
        ],
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
            threshold=float(trigger["threshold"]),
        ):
            triggered_ids.append(trigger["trigger_id"])

    require(
        score["hard_triggered"] == bool(triggered_ids),
        "score.hard_triggered does not match observed signals",
    )
    require(
        set(score["hard_trigger_ids"]) == set(triggered_ids),
        "score.hard_trigger_ids does not match active triggers",
    )

    guards = document["guard_evaluation"]
    policy_guards = policy["guards"]

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
            policy_guards[
                "minimum_shadow_readiness_score"
            ],
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
        "cooldown duration does not match policy",
    )

    expected_active_duration_satisfied = (
        active["active_duration_seconds"]
        >= guards["minimum_active_duration_seconds"]
    )
    expected_maximum_duration_reached = (
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
    expected_cooldown_satisfied = (
        guards["cooldown_elapsed_seconds"]
        >= guards["cooldown_seconds"]
    )

    require(
        guards["active_duration_satisfied"]
        == expected_active_duration_satisfied,
        "active_duration_satisfied is inconsistent",
    )
    require(
        guards["maximum_duration_reached"]
        == expected_maximum_duration_reached,
        "maximum_duration_reached is inconsistent",
    )
    require(
        guards["shadow_readiness_satisfied"]
        == expected_shadow_ready,
        "shadow_readiness_satisfied is inconsistent",
    )
    require(
        guards["regeneration_completion_satisfied"]
        == expected_regeneration_ready,
        "regeneration_completion_satisfied is inconsistent",
    )
    require(
        guards["cooldown_satisfied"]
        == expected_cooldown_satisfied,
        "cooldown_satisfied is inconsistent",
    )

    blockers_absent = not guards["handoff_blockers"]

    expected_guards_passed = (
        expected_active_duration_satisfied
        and expected_shadow_ready
        and expected_regeneration_ready
        and expected_cooldown_satisfied
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
    rotation_actions = {
        "ROTATE_NOW",
        "ROTATE_AT",
        "EMERGENCY_REASSIGN",
    }

    if decision["action"] in rotation_actions:
        require(
            decision["selected_assuming_unit_id"]
            == assuming["unit_id"],
            "selected assuming unit does not match candidate",
        )
        require(
            decision["selected_continuity_unit_id"]
            == continuity["unit_id"],
            "selected continuity unit does not match candidate",
        )
        require(
            decision["planned_handoff_id"] is not None,
            "rotation action requires planned_handoff_id",
        )

    threshold_rotation_required = (
        score["total_score"] >= score["rotation_score"]
        and score["consecutive_threshold_breaches"]
        >= score["required_consecutive_breaches"]
    )

    fairness_policy = policy["fairness"]
    fairness_debt = raw_values.get("fairness_debt", 0.0)

    fairness_rotation_required = (
        fairness_policy["enabled"]
        and (
            active["consecutive_active_shifts"]
            >= fairness_policy[
                "maximum_consecutive_active_shifts"
            ]
            or active["active_share_in_window"]
            > fairness_policy["maximum_active_share"]
            or fairness_debt
            >= fairness_policy[
                "force_rotation_debt_threshold"
            ]
        )
    )

    rotation_required = (
        threshold_rotation_required
        or expected_maximum_duration_reached
        or score["hard_triggered"]
        or fairness_rotation_required
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
            "rotation is required and guards pass, but "
            "the decision does not rotate or abort",
        )

    if (
        decision["action"] == "HOLD"
        and rotation_required
        and guards["all_required_guards_passed"]
    ):
        raise SemanticValidationError(
            "HOLD is invalid when rotation is required "
            "and all guards pass"
        )


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

    wing_ids = [
        wing["wing_id"]
        for wing in wing_definitions
    ]
    require_unique(wing_ids, "wing_definitions.wing_id")

    wing_map = {
        wing["wing_id"]: wing
        for wing in wing_definitions
    }

    domain_ids = [
        domain["domain_id"]
        for domain in rotation_domains
    ]
    require_unique(domain_ids, "rotation_domains.domain_id")

    domain_map = {
        domain["domain_id"]: domain
        for domain in rotation_domains
    }

    assignment_ids = [
        assignment["assignment_id"]
        for assignment in assignments
    ]
    require_unique(
        assignment_ids,
        "assignments.assignment_id",
    )

    assigned_wing_ids = [
        assignment["wing_id"]
        for assignment in assignments
    ]
    require_unique(
        assigned_wing_ids,
        "assignments.wing_id",
    )

    require(
        set(assigned_wing_ids) == set(wing_map),
        "every declared Wing must have exactly one assignment",
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
            f"rotation domain {domain['domain_id']} must use "
            "three distinct groups",
        )

        require_unique(
            domain["wing_ids"],
            f"rotation domain {domain['domain_id']} wing_ids",
        )

        for wing_id in domain["wing_ids"]:
            require(
                wing_id in wing_map,
                f"domain {domain['domain_id']} references "
                f"unknown Wing {wing_id}",
            )
            require(
                wing_id not in wing_domain_map,
                f"Wing {wing_id} belongs to multiple "
                "rotation domains",
            )

            wing_domain_map[wing_id] = domain["domain_id"]

    require(
        set(wing_domain_map) == set(wing_map),
        "every Wing must belong to exactly one rotation domain",
    )

    for domain_id, domain in domain_map.items():
        expected_wings = set(domain["wing_ids"])

        actual_wings = {
            assignment["wing_id"]
            for assignment in assignments
            if assignment["domain_id"] == domain_id
        }

        require(
            actual_wings == expected_wings,
            f"rotation domain {domain_id} Wing declarations "
            "do not match assignments",
        )

    all_slots_rotation_ready = True
    critical_fully_covered = 0

    for assignment in assignments:
        wing_id = assignment["wing_id"]
        domain_id = assignment["domain_id"]

        require(
            wing_id in wing_map,
            f"assignment references unknown Wing {wing_id}",
        )
        require(
            domain_id in domain_map,
            f"assignment references unknown domain {domain_id}",
        )
        require(
            wing_domain_map[wing_id] == domain_id,
            f"Wing {wing_id} is assigned to the wrong domain",
        )

        wing = wing_map[wing_id]
        domain = domain_map[domain_id]

        active = assignment["active_slot"]
        shadow = assignment["shadow_slot"]
        regeneration = assignment["regeneration_slot"]

        require(
            active["group_id"] == domain["active_group_id"],
            f"{wing_id}: active slot group_id is incorrect",
        )
        require(
            shadow["group_id"] == domain["shadow_group_id"],
            f"{wing_id}: shadow slot group_id is incorrect",
        )
        require(
            regeneration["group_id"]
            == domain["regeneration_group_id"],
            f"{wing_id}: regeneration slot group_id is incorrect",
        )

        temporal_member_ids = {
            active["member_id"],
            shadow["member_id"],
            regeneration["member_id"],
        }

        if not constraints["allow_same_member_across_states"]:
            require(
                len(temporal_member_ids) == 3,
                f"{wing_id}: Active, Shadow, and Regeneration "
                "must use distinct members",
            )

        required_capabilities = set(
            wing["required_capabilities"]
        )

        for slot_name, slot in (
            ("active", active),
            ("shadow", shadow),
            ("regeneration", regeneration),
        ):
            slot_capabilities = set(slot["capabilities"])

            require(
                required_capabilities.issubset(
                    slot_capabilities
                ),
                f"{wing_id}: {slot_name} slot is missing "
                "required capabilities",
            )

        shadow_ready = (
            shadow["takeover_readiness_score"]
            >= constraints[
                "minimum_shadow_takeover_readiness_score"
            ]
        )
        shadow_synchronized = (
            shadow["synchronization_score"]
            >= constraints[
                "minimum_shadow_synchronization_score"
            ]
        )
        regeneration_complete = (
            regeneration["regeneration_completion_score"]
            >= constraints[
                "minimum_regeneration_completion_score"
            ]
        )

        require(
            shadow_ready,
            f"{wing_id}: Shadow takeover readiness is too low",
        )
        require(
            shadow_synchronized,
            f"{wing_id}: Shadow synchronization is too low",
        )
        require(
            regeneration_complete,
            f"{wing_id}: Regeneration completion is too low",
        )

        slot_health_ok = all(
            slot["health_state"] != "BLOCKED"
            for slot in (
                active,
                shadow,
                regeneration,
            )
        )

        all_slots_rotation_ready = (
            all_slots_rotation_ready
            and shadow_ready
            and shadow_synchronized
            and regeneration_complete
            and slot_health_ok
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
                    f"critical Wing {wing_id} must use "
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
                    f"critical Wing {wing_id} must use "
                    "three distinct regions",
                )

            if (
                slot_health_ok
                and shadow_ready
                and shadow_synchronized
                and regeneration_complete
            ):
                critical_fully_covered += 1

    dependency_ids = [
        dependency["dependency_id"]
        for dependency in dependencies
    ]
    require_unique(
        dependency_ids,
        "dependencies.dependency_id",
    )

    for dependency in dependencies:
        source = dependency["source_wing_id"]
        target = dependency["target_wing_id"]

        require(
            source in wing_map,
            f"dependency references unknown source Wing {source}",
        )
        require(
            target in wing_map,
            f"dependency references unknown target Wing {target}",
        )
        require(
            source != target,
            f"dependency {dependency['dependency_id']} cannot "
            "reference the same Wing as source and target",
        )

        if not constraints["allow_cross_domain_dependencies"]:
            require(
                wing_domain_map[source]
                == wing_domain_map[target],
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

    expected_rotation_ready = (
        coverage_ratio == 1.0
        and critical_coverage_ratio
        >= constraints["minimum_critical_coverage_ratio"]
        and all_slots_rotation_ready
        and not matrix_health["blocking_conflicts"]
    )

    require(
        matrix_health["rotation_ready"]
        == expected_rotation_ready,
        "matrix_health.rotation_ready is inconsistent",
    )


def resolve_receipt_matrix_constraints(
    document: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any] | None:
    """Resolve matrix constraints referenced by a receipt when available."""

    matrices = context["matrices"]

    for reference in document["source_records"]["matrix_record_refs"]:
        matrix_id = reference_tail(reference)

        if matrix_id in matrices:
            return matrices[matrix_id]["constraints"]

    return None


def validate_continuous_operation_receipt_semantics(
    document: dict[str, Any],
    context: dict[str, Any],
) -> None:
    """Validate Continuous Operation Receipt invariants."""

    period = document["period"]

    started_at = parse_datetime(
        period["started_at"],
        "period.started_at",
    )
    ended_at = parse_datetime(
        period["ended_at"],
        "period.ended_at",
    )

    require(
        started_at < ended_at,
        "period.started_at must be earlier than period.ended_at",
    )

    expected_duration = int(
        (ended_at - started_at).total_seconds()
    )

    require(
        period["duration_seconds"] == expected_duration,
        "period.duration_seconds does not match period boundaries",
    )

    rotation_summary = document["rotation_summary"]
    domain_rotations = rotation_summary["domain_rotations"]

    completed_rotations = sum(
        1
        for rotation in domain_rotations
        if rotation["status"] == "COMPLETED"
    )

    aborted_rotations = sum(
        1
        for rotation in domain_rotations
        if rotation["status"] in {"ABORTED", "ROLLED_BACK"}
    )

    require(
        rotation_summary["completed_rotations"]
        == completed_rotations,
        "rotation_summary.completed_rotations is incorrect",
    )
    require(
        rotation_summary["aborted_rotations"]
        == aborted_rotations,
        "rotation_summary.aborted_rotations is incorrect",
    )
    require(
        rotation_summary["planned_rotations"]
        == len(domain_rotations),
        "rotation_summary.planned_rotations must match "
        "domain_rotations count",
    )

    for rotation in domain_rotations:
        participant_ids = {
            rotation["releasing_group_id"],
            rotation["assuming_group_id"],
            rotation["continuity_group_id"],
        }

        require(
            len(participant_ids) == 3,
            f"domain rotation {rotation['domain_id']} must use "
            "three distinct groups",
        )

        if rotation["status"] == "COMPLETED":
            require(
                rotation["duplicate_primary_detected"] is False,
                f"completed domain rotation "
                f"{rotation['domain_id']} cannot contain "
                "duplicate primary authority",
            )

    continuity = document["continuity_outcome"]

    expected_maximum_gap = max(
        (
            rotation["authority_gap_ms"]
            for rotation in domain_rotations
        ),
        default=0,
    )

    require(
        continuity["maximum_observed_gap_ms"]
        == expected_maximum_gap,
        "continuity maximum_observed_gap_ms is incorrect",
    )

    authority_conflicts = sum(
        1
        for rotation in domain_rotations
        if rotation["duplicate_primary_detected"]
    )

    require(
        continuity["authority_conflict_events"]
        == authority_conflicts,
        "continuity authority_conflict_events is incorrect",
    )

    require(
        continuity["duplicate_execution_events"]
        >= authority_conflicts,
        "duplicate_execution_events cannot be lower than "
        "detected authority conflicts",
    )

    duration_ms = period["duration_seconds"] * 1000

    expected_availability = (
        (
            duration_ms
            - continuity["total_interruption_ms"]
        )
        / duration_ms
        * 100
    )

    require(
        approximately_equal(
            continuity["availability_percent"],
            expected_availability,
            tolerance=1e-5,
        ),
        "continuity availability_percent is incorrect",
    )

    expected_slo_met = (
        continuity["availability_percent"]
        >= continuity["continuity_slo_percent"]
    )

    require(
        continuity["continuity_slo_met"]
        == expected_slo_met,
        "continuity_slo_met is inconsistent",
    )

    if continuity["service_status"] == "CONTINUOUS":
        require(
            continuity["continuity_slo_met"] is True,
            "CONTINUOUS service status requires the continuity SLO",
        )
        require(
            continuity["authority_conflict_events"] == 0,
            "CONTINUOUS service cannot contain authority conflicts",
        )

    load_distribution = document["load_distribution"]
    unit_outcomes = load_distribution["units"]

    unit_ids = [unit["unit_id"] for unit in unit_outcomes]
    require_unique(
        unit_ids,
        "load_distribution.units.unit_id",
    )

    expected_tasks = sum(
        unit["tasks_completed"]
        for unit in unit_outcomes
    )

    require(
        load_distribution["total_tasks_completed"]
        == expected_tasks,
        "load_distribution.total_tasks_completed is incorrect",
    )

    compute_share_total = sum(
        float(unit["compute_work_share"])
        for unit in unit_outcomes
    )
    before_share_total = sum(
        float(unit["active_share_before"])
        for unit in unit_outcomes
    )
    after_share_total = sum(
        float(unit["active_share_after"])
        for unit in unit_outcomes
    )

    require(
        approximately_equal(compute_share_total, 1.0),
        "compute work shares must sum to 1.0",
    )
    require(
        approximately_equal(before_share_total, 1.0),
        "active shares before rotation must sum to 1.0",
    )
    require(
        approximately_equal(after_share_total, 1.0),
        "active shares after rotation must sum to 1.0",
    )

    require(
        approximately_equal(
            load_distribution["compute_share_total"],
            compute_share_total,
        ),
        "load_distribution.compute_share_total is incorrect",
    )
    require(
        approximately_equal(
            load_distribution["active_share_before_total"],
            before_share_total,
        ),
        "active_share_before_total is incorrect",
    )
    require(
        approximately_equal(
            load_distribution["active_share_after_total"],
            after_share_total,
        ),
        "active_share_after_total is incorrect",
    )

    fairness = document["fairness_outcome"]

    before_shares = [
        float(unit["active_share_before"])
        for unit in unit_outcomes
    ]
    after_shares = [
        float(unit["active_share_after"])
        for unit in unit_outcomes
    ]

    expected_concentration_before = sum(
        share**2
        for share in before_shares
    )
    expected_concentration_after = sum(
        share**2
        for share in after_shares
    )
    expected_spread_before = (
        max(before_shares) - min(before_shares)
    )
    expected_spread_after = (
        max(after_shares) - min(after_shares)
    )

    require(
        approximately_equal(
            fairness["concentration_index_before"],
            expected_concentration_before,
            tolerance=1e-5,
        ),
        "fairness concentration_index_before is incorrect",
    )
    require(
        approximately_equal(
            fairness["concentration_index_after"],
            expected_concentration_after,
            tolerance=1e-5,
        ),
        "fairness concentration_index_after is incorrect",
    )
    require(
        approximately_equal(
            fairness["active_share_spread_before"],
            expected_spread_before,
            tolerance=1e-5,
        ),
        "fairness active_share_spread_before is incorrect",
    )
    require(
        approximately_equal(
            fairness["active_share_spread_after"],
            expected_spread_after,
            tolerance=1e-5,
        ),
        "fairness active_share_spread_after is incorrect",
    )

    expected_fairness_improved = (
        expected_concentration_after
        < expected_concentration_before
        and expected_spread_after
        <= expected_spread_before
    )

    require(
        fairness["fairness_improved"]
        == expected_fairness_improved,
        "fairness_improved is inconsistent",
    )

    expected_above_maximum = {
        unit["unit_id"]
        for unit in unit_outcomes
        if unit["active_share_after"]
        > fairness["maximum_active_share"]
    }

    require(
        set(fairness["units_above_maximum_share"])
        == expected_above_maximum,
        "units_above_maximum_share is incorrect",
    )

    regeneration = document["regeneration_outcome"]
    regeneration_units = regeneration["units"]

    regeneration_unit_ids = [
        unit["unit_id"]
        for unit in regeneration_units
    ]
    require_unique(
        regeneration_unit_ids,
        "regeneration_outcome.units.unit_id",
    )

    expected_average_completion = (
        sum(
            float(unit["completion_score"])
            for unit in regeneration_units
        )
        / len(regeneration_units)
    )

    require(
        approximately_equal(
            regeneration["average_completion_score"],
            expected_average_completion,
            tolerance=1e-5,
        ),
        "regeneration average_completion_score is incorrect",
    )

    expected_regeneration_complete = all(
        unit["completion_score"]
        >= regeneration[
            "minimum_required_completion_score"
        ]
        and not unit["actions_failed"]
        and unit["blocking_issue_count"] == 0
        and unit["returned_to_shadow"] is True
        for unit in regeneration_units
    )

    require(
        regeneration["all_required_regeneration_complete"]
        == expected_regeneration_complete,
        "all_required_regeneration_complete is inconsistent",
    )

    matrix_constraints = resolve_receipt_matrix_constraints(
        document,
        context,
    )

    if matrix_constraints is None:
        shadow_readiness_threshold = 0.90
        shadow_sync_threshold = 0.90
        regeneration_threshold = 0.90
    else:
        shadow_readiness_threshold = matrix_constraints[
            "minimum_shadow_takeover_readiness_score"
        ]
        shadow_sync_threshold = matrix_constraints[
            "minimum_shadow_synchronization_score"
        ]
        regeneration_threshold = matrix_constraints[
            "minimum_regeneration_completion_score"
        ]

    wing_outcomes = document["wing_outcomes"]
    wings = wing_outcomes["wings"]

    wing_ids = [wing["wing_id"] for wing in wings]
    require_unique(
        wing_ids,
        "wing_outcomes.wings.wing_id",
    )

    total_wings = len(wings)

    critical_wings = sum(
        1
        for wing in wings
        if wing["criticality"] == "CRITICAL"
    )

    fully_covered_wings = 0
    fully_covered_critical_wings = 0

    for wing in wings:
        temporal_members = {
            wing["active_member_id"],
            wing["shadow_member_id"],
            wing["regeneration_member_id"],
        }

        require(
            len(temporal_members) == 3,
            f"Wing {wing['wing_id']} must use three distinct "
            "temporal members",
        )

        expected_fully_covered = (
            wing["active_health"] != "BLOCKED"
            and wing["shadow_readiness_score"]
            >= shadow_readiness_threshold
            and wing["shadow_synchronization_score"]
            >= shadow_sync_threshold
            and wing["regeneration_completion_score"]
            >= regeneration_threshold
            and wing["blocking_event_count"] == 0
        )

        require(
            wing["fully_covered"]
            == expected_fully_covered,
            f"Wing {wing['wing_id']} fully_covered is inconsistent",
        )

        if expected_fully_covered:
            fully_covered_wings += 1

            if wing["criticality"] == "CRITICAL":
                fully_covered_critical_wings += 1

    coverage_ratio = (
        fully_covered_wings / total_wings
        if total_wings
        else 0.0
    )

    critical_coverage_ratio = (
        fully_covered_critical_wings / critical_wings
        if critical_wings
        else 1.0
    )

    require(
        wing_outcomes["total_wings"] == total_wings,
        "wing_outcomes.total_wings is incorrect",
    )
    require(
        wing_outcomes["critical_wings"] == critical_wings,
        "wing_outcomes.critical_wings is incorrect",
    )
    require(
        wing_outcomes["fully_covered_wings"]
        == fully_covered_wings,
        "wing_outcomes.fully_covered_wings is incorrect",
    )
    require(
        wing_outcomes["fully_covered_critical_wings"]
        == fully_covered_critical_wings,
        "fully_covered_critical_wings is incorrect",
    )
    require(
        approximately_equal(
            wing_outcomes["coverage_ratio"],
            coverage_ratio,
        ),
        "wing_outcomes.coverage_ratio is incorrect",
    )
    require(
        approximately_equal(
            wing_outcomes["critical_coverage_ratio"],
            critical_coverage_ratio,
        ),
        "wing_outcomes.critical_coverage_ratio is incorrect",
    )

    incidents = document["incidents"]
    incident_ids = [
        incident["incident_id"]
        for incident in incidents
    ]
    require_unique(incident_ids, "incidents.incident_id")

    unresolved_blocking_incidents = [
        incident["incident_id"]
        for incident in incidents
        if incident["blocking"] and not incident["resolved"]
    ]

    assessment = document["final_assessment"]

    pass_conditions = (
        rotation_summary["completed_rotations"]
        == rotation_summary["planned_rotations"]
        and rotation_summary["aborted_rotations"] == 0
        and continuity["service_status"] == "CONTINUOUS"
        and continuity["continuity_slo_met"]
        and continuity["duplicate_execution_events"] == 0
        and continuity["authority_conflict_events"] == 0
        and fairness["fairness_improved"]
        and not fairness["units_above_maximum_share"]
        and regeneration[
            "all_required_regeneration_complete"
        ]
        and critical_coverage_ratio == 1.0
        and not unresolved_blocking_incidents
    )

    fail_conditions = (
        continuity["service_status"] == "INTERRUPTED"
        or continuity["authority_conflict_events"] > 0
        or continuity["duplicate_execution_events"] > 0
        or critical_coverage_ratio < 1.0
        or bool(unresolved_blocking_incidents)
    )

    if pass_conditions:
        expected_status = "PASS"
    elif fail_conditions:
        expected_status = "FAIL"
    else:
        expected_status = "WARN"

    require(
        assessment["receipt_status"] == expected_status,
        f"final_assessment.receipt_status should be "
        f"{expected_status}",
    )

    next_action_ids = [
        action["action_id"]
        for action in assessment["next_cycle_actions"]
    ]
    require_unique(
        next_action_ids,
        "final_assessment.next_cycle_actions.action_id",
    )


SEMANTIC_VALIDATORS: dict[str, SemanticValidator] = {
    "validate_shift_state_semantics":
        validate_shift_state_semantics,
    "validate_shift_handoff_semantics":
        validate_shift_handoff_semantics,
    "validate_rotation_policy_semantics":
        validate_rotation_policy_semantics,
    "validate_rotation_evaluation_semantics":
        validate_rotation_evaluation_semantics,
    "validate_multi_wing_matrix_semantics":
        validate_multi_wing_matrix_semantics,
    "validate_continuous_operation_receipt_semantics":
        validate_continuous_operation_receipt_semantics,
}


def validate_schema(
    *,
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

    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        print(f"[schema-definition-error] {exc}")
        return False, example

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )

    errors = sorted(
        validator.iter_errors(example),
        key=lambda error: (
            list(error.absolute_path),
            error.message,
        ),
    )

    if errors:
        for error in errors:
            location = format_error_path(error)
            print(
                f"[schema-error] {location}: "
                f"{error.message}"
            )

        return False, example

    print("[schema-ok]")
    return True, example


def build_context(
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build cross-document indexes for semantic validation."""

    policies: dict[str, dict[str, Any]] = {}
    matrices: dict[str, dict[str, Any]] = {}
    documents_by_record_id: dict[str, dict[str, Any]] = {}

    for document in documents:
        record_type = document.get("record_type")

        if record_type == "adaptive_rotation_policy":
            policies[document["policy_id"]] = document

        if record_type == "multi_wing_shift_matrix":
            matrices[document["matrix_id"]] = document

        record_id = (
            document.get("record_id")
            or document.get("evaluation_id")
            or document.get("matrix_id")
            or document.get("receipt_id")
            or document.get("policy_id")
        )

        if isinstance(record_id, str):
            documents_by_record_id[record_id] = document

    return {
        "policies": policies,
        "matrices": matrices,
        "documents_by_record_id": documents_by_record_id,
    }


def run_semantic_validation(
    *,
    target: dict[str, Any],
    document: dict[str, Any],
    context: dict[str, Any],
) -> bool:
    """Run one target's protocol-level semantic validator."""

    validator_name = target["semantic_validator"]

    if validator_name is None:
        return True

    print(f"[semantic] {target['name']}")

    semantic_validator = SEMANTIC_VALIDATORS.get(
        validator_name
    )

    if semantic_validator is None:
        print(
            f"[semantic-error] unknown semantic validator: "
            f"{validator_name}"
        )
        return False

    try:
        semantic_validator(document, context)
    except SemanticValidationError as exc:
        print(f"[semantic-error] {exc}")
        return False
    except KeyError as exc:
        print(
            f"[semantic-error] missing required field during "
            f"semantic validation: {exc}"
        )
        return False
    except (TypeError, ValueError) as exc:
        print(f"[semantic-error] invalid field value: {exc}")
        return False

    print("[semantic-ok]")
    return True


def main() -> int:
    """Validate every protocol example."""

    print("=== Tri-Shift AI Rotation Protocol Validation ===")
    print()

    loaded_targets: list[
        tuple[dict[str, Any], dict[str, Any]]
    ] = []

    loaded_documents: list[dict[str, Any]] = []
    schema_validation_passed = True
    semantic_validation_passed = True

    try:
        for target in VALIDATION_TARGETS:
            schema_valid, document = validate_schema(
                name=target["name"],
                schema_path=target["schema"],
                example_path=target["example"],
            )

            schema_validation_passed = (
                schema_validation_passed
                and schema_valid
            )

            if document is not None:
                loaded_documents.append(document)
                loaded_targets.append((target, document))

            print()

    except RuntimeError as exc:
        print(f"[fatal] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            f"[fatal] unexpected schema validation failure: "
            f"{exc}",
            file=sys.stderr,
        )
        return 2

    if not schema_validation_passed:
        print(
            "Schema validation failed. "
            "Semantic validation was not executed."
        )
        return 1

    context = build_context(loaded_documents)

    try:
        for target, document in loaded_targets:
            valid = run_semantic_validation(
                target=target,
                document=document,
                context=context,
            )

            semantic_validation_passed = (
                semantic_validation_passed
                and valid
            )

            print()

    except Exception as exc:
        print(
            f"[fatal] unexpected semantic validation failure: "
            f"{exc}",
            file=sys.stderr,
        )
        return 2

    if not semantic_validation_passed:
        print("Semantic validation failed.")
        return 1

    print("All examples are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
