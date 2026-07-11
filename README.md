# Tri-Shift AI Rotation Protocol

A protocol for continuous AI operation through rotating active, shadow, and regeneration shifts across distributed agents and model replicas.

## Overview

The Tri-Shift AI Rotation Protocol defines a time-based workload rotation structure for distributed AI systems.

Instead of requiring the same model, agent group, or compute cluster to remain continuously active, the system rotates operational responsibility across three shift states:

* `ACTIVE`
* `REGENERATION`
* `SHADOW`

The whole AI system remains continuously available, while individual units periodically change their operational role.

This is not a sleep protocol.

It is a continuous-operation protocol based on rotating responsibility, observation, and internal maintenance.

## Core Principle

```text
The system remains active.
The same unit does not remain active indefinitely.
```

At any given time, different units may perform different temporal roles:

```text
Unit A: ACTIVE
Unit B: SHADOW
Unit C: REGENERATION
```

After rotation:

```text
Unit A: REGENERATION
Unit B: ACTIVE
Unit C: SHADOW
```

After the next rotation:

```text
Unit A: SHADOW
Unit B: REGENERATION
Unit C: ACTIVE
```

The canonical unit-level cycle is:

```text
ACTIVE
  ↓
REGENERATION
  ↓
SHADOW
  ↓
ACTIVE
```

This order is intentional.

After active service, a unit first enters regeneration to reduce accumulated pressure and repair internal state. It then enters shadow operation to observe the current active unit, synchronize context, and prepare for the next active shift.

## Shift States

### ACTIVE

The unit holds primary service authority.

Typical duties include:

* user-facing inference
* real-time decision-making
* external tool execution
* task orchestration
* trace generation
* high-priority request handling

An `ACTIVE` unit may accept primary external requests.

### REGENERATION

The unit is removed from primary external service and performs internal maintenance.

Typical duties include:

* memory compression
* cache cleanup
* trace organization
* integrity verification
* drift detection
* state reconciliation
* model or agent repair
* resource and thermal recovery

A `REGENERATION` unit is not inactive. Internal maintenance is its assigned work.

### SHADOW

The unit observes the active shift and prepares to assume service authority.

Typical duties include:

* reading current traces
* validating active outputs
* synchronizing operational context
* monitoring unresolved tasks
* preparing handoff state
* maintaining takeover readiness

A `SHADOW` unit does not normally hold primary service authority, but may be used as a standby unit.

## Why Three Shifts

A two-state system usually provides only:

```text
ACTIVE
INACTIVE
```

This creates a direct transition between service and rest, leaving no dedicated state for:

* context synchronization
* handoff preparation
* output observation
* takeover readiness
* pre-activation validation

The third shift creates a temporal buffer.

```text
ACTIVE       = execution
REGENERATION = maintenance
SHADOW       = observation and preparation
```

The shadow shift is therefore not redundant capacity. It is the continuity layer between internal recovery and primary responsibility.

## v0.1 — Shift State Record

Version 0.1 introduces the `Shift State Record`.

The record describes:

* which unit is being observed
* its current shift state
* its previous and planned next state
* its service authority
* the current state window
* assigned and prohibited duties
* load and health conditions
* handoff readiness
* the rotation policy
* audit metadata

Each record represents one unit at one point in the rotation cycle.

## Canonical State Sequence

Version 0.1 uses the following canonical transition sequence:

```text
SHADOW → ACTIVE → REGENERATION → SHADOW
```

Expressed from the active state:

```text
ACTIVE → REGENERATION → SHADOW → ACTIVE
```

The schema validates this sequence.

Emergency transitions, skipped states, and dynamic reassignment are intentionally outside the scope of v0.1. They may be introduced by a later adaptive rotation specification.

## Service Authority

Each shift state has a corresponding service authority:

| Shift state    | Service authority |
| -------------- | ----------------- |
| `ACTIVE`       | `PRIMARY`         |
| `SHADOW`       | `STANDBY`         |
| `REGENERATION` | `INTERNAL_ONLY`   |

This prevents a unit from claiming primary authority while it is supposed to be undergoing maintenance or shadow synchronization.

## Design Invariants

A conforming implementation should preserve the following principles:

1. The system may remain continuously operational.
2. No individual unit should remain permanently assigned to the active shift.
3. Shadow operation is an active observation state, not an idle state.
4. Regeneration is an internal maintenance assignment, not merely shutdown.
5. Every state transition should be recorded.
6. Shift records should be immutable after finalization.
7. Handoff readiness should be visible before service authority changes.
8. Rotation should distribute temporal pressure as well as computational load.

## Example Lifecycle

```text
Rotation cycle: cycle-001

T1
A = ACTIVE
B = SHADOW
C = REGENERATION

T2
A = REGENERATION
B = ACTIVE
C = SHADOW

T3
A = SHADOW
B = REGENERATION
C = ACTIVE

T4
A = ACTIVE
B = SHADOW
C = REGENERATION
```

The service remains available throughout the cycle, but no single unit carries the same type of load continuously.

## Validation

Install the validation dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python scripts/validate_examples.py
```

Expected output:

```text
[validate] Shift State Record
  schema : schemas/shift-state-record.schema.json
  example: examples/shift-state-record.example.yaml
[ok] shift-state-record.example.yaml is valid
```

## Scope

Version 0.1 defines only the state record for an individual shift unit.

It does not yet define:

* full handoff payloads
* unfinished task transfer
* trace-delta transfer
* emergency takeover
* adaptive rotation timing
* multi-wing shift matrices
* cluster-wide balance enforcement
* continuous-operation receipts

These concerns are reserved for later versions.

## Version Roadmap

```text
v0.1 — Shift State Record
v0.2 — Shift Handoff Record
v0.3 — Adaptive Rotation Policy
v0.4 — Multi-Wing Shift Matrix
v0.5 — Continuous Operation Receipt
```

## Civilizational Position

Traditional load balancing distributes requests across machines.

Tri-shift rotation distributes responsibility across time.

```text
Load balancing:
Where should this task run?

Tri-shift rotation:
Which unit should bear this kind of responsibility now?
```

The protocol therefore treats time, responsibility, observation, and regeneration as first-class parts of distributed AI architecture.

The goal is not to make AI sleep like a human.

The goal is to prevent continuous operation from becoming continuous concentration.

```text
The AI system remains awake.
Its responsibilities circulate.
```
