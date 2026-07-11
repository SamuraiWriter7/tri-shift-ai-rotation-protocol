# Changelog

All notable changes to the Tri-Shift AI Rotation Protocol are documented in this file.

The project follows semantic versioning where applicable.

## [Unreleased]

### Planned

Possible derived work after the first protocol arc includes:

* cross-system shift federation
* geographic and provider rotation
* energy and economic cost receipts
* long-term fairness history
* human–AI mixed shift structures
* emergency reserve-shift protocols
* inter-organizational handoff
* Royalty and contribution allocation bridges

## [0.5.0] - 2026-07-12

### Added

* Introduced the `Continuous Operation Receipt`.
* Added bounded operating-period declarations.
* Added source-record binding for:

  * Shift State Records
  * Shift Handoff Records
  * Rotation Evaluation Records
  * Multi-Wing Shift Matrices
* Added planned, completed, aborted, and emergency rotation totals.
* Added domain-level rotation summaries.
* Added releasing, assuming, and continuity group declarations.
* Added authority-gap measurement.
* Added duplicate-primary detection.
* Added rollback-use declarations.
* Added continuity outcomes for:

  * service status
  * availability
  * total interruption duration
  * maximum transition gap
  * duplicate execution
  * authority conflicts
  * continuity SLO compliance
* Added unit-level load-distribution outcomes.
* Added Active-duty shares before and after rotation.
* Added compute-work shares.
* Added completed-task totals.
* Added fairness-debt outcomes.
* Added Active-share concentration measurement.
* Added Active-share spread measurement.
* Added maximum Active-share violation reporting.
* Added unit-level Regeneration outcomes.
* Added maintenance-action success and failure records.
* Added Regeneration completion scoring.
* Added return-to-Shadow confirmation.
* Added final Multi-Wing coverage outcomes.
* Added independent critical-Wing coverage measurement.
* Added incident preservation.
* Added final cycle assessment:

  * `PASS`
  * `WARN`
  * `FAIL`
* Added next-cycle corrective actions.
* Added previous-receipt references.
* Added evidence-bundle references.

### Validation

The v0.5 semantic validator verifies:

* operating-period duration
* planned and completed rotation counts
* distinct rotation participants
* maximum authority gap
* authority-conflict totals
* service availability calculation
* continuity SLO evaluation
* completed-task totals
* compute-work-share totals
* Active-duty-share totals
* fairness concentration values
* Active-share spread values
* fairness-improvement declarations
* maximum Active-share violations
* average Regeneration score
* Regeneration-completion state
* Wing-count totals
* critical-Wing totals
* full-coverage totals
* total coverage ratio
* critical coverage ratio
* distinct temporal Wing members
* Wing full-coverage declarations
* unresolved blocking incidents
* final Receipt status

### Design Decision

Version 0.5 separates uptime from sustainable continuity.

```text
Uptime:
the service did not stop

Sustainable continuity:
the service did not stop,
authority did not conflict,
responsibility circulated,
units regenerated,
and critical roles remained covered
```

A system may report high availability while receiving a `WARN` or `FAIL` Receipt if responsibility remains structurally concentrated.

### Structural Change

The first protocol arc is complete:

```text
v0.1
Shift State Record

v0.2
Shift Handoff Record

v0.3
Adaptive Rotation Policy

v0.4
Multi-Wing Shift Matrix

v0.5
Continuous Operation Receipt
```

Together, they define:

```text
State
  +
Transition
  +
Decision
  +
Functional allocation
  +
Cycle audit
```

### First-Arc Completion

Version 0.5 completes the initial specification arc.

Future development should preferably proceed through derived repositories or a second protocol arc rather than indefinitely expanding the first record family.

## [0.4.0] - 2026-07-12

### Added

* Introduced the `Multi-Wing Shift Matrix`.
* Connected Multi-Wing functional roles with tri-shift temporal states.
* Added Wing definitions for:

  * Finder
  * Analyst
  * Planner
  * Executor
  * Verifier
  * Boundary
  * Bridge
  * Router
  * Trace Core
  * Memory
  * Repair
  * Auditor
  * custom Wings
* Added Wing criticality levels:

  * `OPTIONAL`
  * `SUPPORTING`
  * `CRITICAL`
* Added required-capability declarations.
* Added allowed-output boundaries.
* Added prohibited-output boundaries.
* Added human-gate requirements.
* Added Active, Shadow, and Regeneration slot assignments.
* Added Wing-specific health states.
* Added takeover-readiness scores.
* Added Shadow synchronization scores.
* Added Regeneration completion scores.
* Added role-specific maintenance-action declarations.
* Added Rotation Domains.
* Added Atomic and Staged domain modes.
* Added domain-based partial rotation.
* Added cross-Wing dependency declarations.
* Added dependency types for:

  * data
  * control
  * validation
  * safety
  * trace
  * memory
  * routing
* Added provider-diversity constraints.
* Added region-diversity constraints.
* Added critical-Wing coverage measurement.
* Added matrix-level rotation-readiness evaluation.
* Added blocking-conflict declarations.
* Added matrix warnings.

### Validation

The v0.4 semantic validator verifies:

* Wing IDs are unique
* Rotation Domain IDs are unique
* every Wing belongs to exactly one Rotation Domain
* every Wing has exactly one assignment
* domain Wing declarations match assignment records
* Active, Shadow, and Regeneration groups are distinct
* slot group IDs match their Rotation Domain
* members are distinct across temporal states when required
* every slot satisfies required Wing capabilities
* Shadow takeover readiness meets the configured threshold
* Shadow synchronization meets the configured threshold
* Regeneration completion meets the configured threshold
* critical Wings satisfy provider-diversity rules
* critical Wings satisfy region-diversity rules
* dependency references point to declared Wings
* forbidden cross-domain dependencies are rejected
* matrix coverage values are reproducible
* critical coverage values are reproducible
* rotation-readiness declarations match the matrix state

### Design Decision

Version 0.4 introduces Rotation Domains rather than requiring every Wing in the system to rotate globally at the same time.

```text
Global synchronization
        ↓
high coupling and unnecessary rotation

Rotation Domains
        ↓
localized responsibility circulation
```

Different functional regions may therefore rotate according to their own pressure and readiness.

### Structural Change

The protocol now contains two orthogonal control axes:

```text
Role axis:
Finder → Analyst → Executor → Verifier → Boundary → Trace

Time axis:
Active → Regeneration → Shadow → Active
```

The resulting matrix makes functional concentration and temporal concentration auditable.

### Scope Limitations

Version 0.4 does not define:

* full-cycle continuity receipts
* historical fairness summaries
* aggregate energy outcomes
* long-term Wing performance
* complete service-level compliance reports

These concerns are introduced in v0.5.

## [0.3.0] - 2026-07-12

### Added

* Introduced the `Adaptive Rotation Policy`.
* Introduced the `Rotation Evaluation Record`.
* Added Scheduled, Adaptive, and Hybrid rotation modes.
* Added configurable evaluation intervals.
* Added rolling evaluation windows.
* Added weighted operational signals.
* Added support for:

  * compute pressure
  * memory pressure
  * queue pressure
  * error pressure
  * trace accumulation
  * context staleness
  * fairness debt
* Added warning and critical signal thresholds.
* Added normalized weighted-sum scoring.
* Added consecutive-threshold-breach requirements.
* Added emergency hard triggers.
* Added rotation actions:

  * `HOLD`
  * `ROTATE_NOW`
  * `ROTATE_AT`
  * `EMERGENCY_REASSIGN`
  * `ABORT_ACTIVE_WORK`
* Added minimum and maximum Active-duration guards.
* Added Shadow-readiness guards.
* Added Regeneration-completion guards.
* Added rotation cooldown protection.
* Added handoff-blocker evaluation.
* Added emergency guard overrides.
* Added fairness controls for:

  * consecutive Active shifts
  * rolling Active-duty share
  * fairness-debt thresholds
* Added fallback behavior for:

  * missing required signals
  * unavailable Shadow successors
  * incomplete Regeneration units
  * failed evaluation
* Added immutable rotation-decision records.
* Added cross-document validation between policies and evaluations.

### Validation

The v0.3 semantic validator verifies:

* signal IDs are unique
* signal weights sum to `1.0`
* warning and critical thresholds follow signal direction
* scoring thresholds are correctly ordered
* hard triggers reference defined signals
* required signals are present
* evaluation weights match the selected policy
* score contributions are reproducible
* threshold classifications match observed values
* total scores are reproducible
* hard-trigger declarations match actual observations
* guard thresholds match the selected policy
* successor readiness is calculated correctly
* continuity-unit readiness is calculated correctly
* rotation participants are distinct
* rotation decisions identify valid successor units
* `HOLD` is rejected when mandatory rotation conditions are satisfied

### Design Decision

Version 0.3 treats fairness as an operational signal.

A unit may accumulate rotation pressure even when its compute and error metrics remain healthy.

```text
Operational efficiency
        +
Responsibility fairness
        =
Sustainable continuous operation
```

A system should rotate responsibility before concentration becomes structural exhaustion.

### Structural Change

The protocol now distinguishes:

```text
Shift State
    ↓
what role a unit currently holds

Shift Handoff
    ↓
how responsibility moves

Adaptive Rotation
    ↓
why and when it moves
```

### Scope Limitations

Version 0.3 does not define:

* per-Wing temporal allocation
* cross-Wing compatibility constraints
* partial functional rotation
* model capability matching
* provider or region diversity
* full-cycle operation receipts

These concerns are introduced in v0.4 and v0.5.

## [0.2.0] - 2026-07-12

### Added

* Introduced the `Shift Handoff Record`.
* Defined tri-party shift rotation involving:

  * releasing unit
  * assuming unit
  * continuity unit
* Defined the coordinated transitions:

  * `ACTIVE → REGENERATION`
  * `SHADOW → ACTIVE`
  * `REGENERATION → SHADOW`
* Added handoff lifecycle phases:

  * `PREPARING`
  * `FROZEN`
  * `TRANSFERRING`
  * `VERIFYING`
  * `ACCEPTED`
  * `COMPLETED`
  * `ABORTED`
* Added trace-checkpoint transfer.
* Added Active-task ownership transfer.
* Added unresolved-decision transfer.
* Added memory-delta references.
* Added external-commitment declarations.
* Added tool-session references.
* Added risk flags.
* Added blocking-state declarations.
* Added non-transferable-item declarations.
* Added authority-transfer modes:

  * `ATOMIC`
  * `TWO_PHASE`
  * `GUARDED`
* Added primary-authority lease records.
* Prohibited dual-primary authority.
* Added explicit incoming-unit acceptance.
* Added independent continuity verification.
* Added service-gap measurement.
* Added duplicate-execution detection.
* Added rollback readiness.
* Added rollback-target records.
* Added protocol-level semantic validation.

### Validation

The v0.2 semantic validator verifies:

* all three participants are distinct
* previous authority holder matches the releasing unit
* next authority holder matches the assuming unit
* rollback target matches the releasing unit
* the continuity unit performs verification
* transferred task ownership matches participant roles
* authority is released before or at acquisition
* completed handoffs contain no blocking tasks
* completed handoffs contain no blocking risks
* completed handoffs contain no duplicate execution
* completed handoffs have been explicitly accepted
* handoff duration remains within the declared maximum

### Design Decision

A handoff is modeled as a three-party responsibility transition rather than a two-party message transfer.

```text
Releasing unit
      ↓
Assuming unit
      ↕
Continuity unit
```

The third participant independently verifies that responsibility, authority, context, and service continuity have moved safely.

### Scope Limitations

Version 0.2 does not define:

* adaptive rotation timing
* pressure thresholds
* fairness scoring
* Wing-level allocation
* long-term cycle audits

These concerns are introduced in later versions.

## [0.1.0] - 2026-07-12

### Added

* Introduced the Tri-Shift AI Rotation Protocol.
* Defined the three canonical shift states:

  * `ACTIVE`
  * `REGENERATION`
  * `SHADOW`
* Defined the canonical rotation sequence:

  * `ACTIVE → REGENERATION → SHADOW → ACTIVE`
* Added the `Shift State Record` JSON Schema.
* Added service-authority bindings:

  * `ACTIVE → PRIMARY`
  * `SHADOW → STANDBY`
  * `REGENERATION → INTERNAL_ONLY`
* Added shift-unit identification for:

  * model replicas
  * agent groups
  * Multi-Wing groups
  * service clusters
  * hybrid units
* Added state-window records.
* Added sequence numbers.
* Added responsibility declarations.
* Added prohibited-duty declarations.
* Added compute-load snapshots.
* Added memory-load snapshots.
* Added queue-depth measurement.
* Added error-rate measurement.
* Added reserved-capacity measurement.
* Added unit health states.
* Added preliminary handoff readiness.
* Added trace-checkpoint references.
* Added Scheduled, Adaptive, and Hybrid policy declarations.
* Added immutable audit metadata.
* Added a valid YAML example.
* Added Python-based JSON Schema validation.
* Added a GitHub Actions validation workflow.

### Validation

The v0.1 validator verifies:

* the example conforms to the JSON Schema
* the shift window is chronologically valid
* planned duration remains within policy limits
* Shift State and service authority remain consistent
* handoff readiness and blockers are consistent
* unit-member IDs are unique

### Design Decision

Version 0.1 adopts:

```text
ACTIVE → REGENERATION → SHADOW → ACTIVE
```

rather than:

```text
ACTIVE → SHADOW → REGENERATION → ACTIVE
```

This ensures that a unit undergoes internal maintenance immediately after primary service and enters Shadow synchronization immediately before returning to Active authority.

### Initial Principle

```text
The system remains active.
The same unit does not remain active indefinitely.
```

Version 0.1 establishes the protocol's central distinction:

```text
Continuous operation
        ≠
permanent responsibility concentration
```
