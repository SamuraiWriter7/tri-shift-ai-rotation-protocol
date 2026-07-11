# Tri-Shift AI Rotation Protocol

A protocol for continuous AI operation through rotating active, shadow, and regeneration shifts across distributed agents, model replicas, and Multi-Wing systems.

## Overview

The Tri-Shift AI Rotation Protocol defines a continuous-operation architecture for distributed AI systems.

Instead of keeping the same model, agent group, compute cluster, or functional role permanently active, operational responsibility circulates across three temporal states:

* `ACTIVE`
* `REGENERATION`
* `SHADOW`

The system as a whole may remain continuously available, while each participating unit periodically changes its responsibility.

This is not an AI sleep protocol.

It is a protocol for preventing continuous operation from becoming continuous concentration.

```text
The system remains active.
The same unit does not remain active indefinitely.
```

## Core Concept

A conventional continuous AI service may distribute requests across multiple replicas while still allowing the same logical structure to carry primary responsibility indefinitely.

Tri-shift rotation distributes not only computational work, but also:

* service authority
* operational responsibility
* observation duties
* maintenance work
* trace synchronization
* recovery time
* verification responsibility

A basic three-unit arrangement is:

```text
Unit A = ACTIVE
Unit B = SHADOW
Unit C = REGENERATION
```

After one rotation:

```text
Unit A = REGENERATION
Unit B = ACTIVE
Unit C = SHADOW
```

After the next rotation:

```text
Unit A = SHADOW
Unit B = REGENERATION
Unit C = ACTIVE
```

The cycle then repeats.

## Canonical Rotation

The canonical unit-level sequence is:

```text
ACTIVE
  ↓
REGENERATION
  ↓
SHADOW
  ↓
ACTIVE
```

Expressed as a complete cycle:

```text
SHADOW → ACTIVE → REGENERATION → SHADOW
```

This order is intentional.

After primary service, a unit first enters Regeneration to reduce accumulated operational pressure and repair internal state.

It then enters Shadow duty to observe the current Active unit, synchronize context, verify current traces, and prepare to assume authority again.

## Shift States

### ACTIVE

The Active unit holds primary service authority.

Typical duties include:

* accepting primary user requests
* real-time inference
* task orchestration
* decision generation
* approved external tool execution
* high-priority request handling
* trace generation
* operational continuity

Canonical authority:

```text
PRIMARY
```

An Active unit may execute externally authorized work.

### REGENERATION

The Regeneration unit is removed from primary external service and assigned internal maintenance duties.

Typical duties include:

* memory compression
* context compaction
* cache cleanup
* trace organization
* checkpoint verification
* integrity inspection
* drift detection
* model or agent repair
* tool-session cleanup
* permission-state review
* resource recovery

Canonical authority:

```text
INTERNAL_ONLY
```

Regeneration is not inactivity.

Internal recovery and structural maintenance are the unit's assigned work.

### SHADOW

The Shadow unit observes the Active shift and prepares to assume primary responsibility.

Typical duties include:

* reading current operational traces
* synchronizing task context
* validating Active outputs
* monitoring unresolved work
* reviewing risk flags
* preparing handoff state
* checking takeover readiness
* maintaining rollback awareness

Canonical authority:

```text
STANDBY
```

A Shadow unit does not normally hold primary authority, but remains operationally prepared.

## Why Three Shifts

A two-state structure normally provides only:

```text
ACTIVE
INACTIVE
```

This leaves no dedicated temporal layer for:

* context synchronization
* handoff preparation
* independent verification
* takeover readiness
* rollback preparation
* pre-activation validation

The third state creates a continuity buffer.

```text
ACTIVE       = execution
REGENERATION = internal maintenance
SHADOW       = observation and preparation
```

The Shadow shift is therefore not redundant capacity.

It is the temporal bridge between Regeneration and Active responsibility.

## Protocol Architecture

The first protocol arc contains five version layers.

```text
v0.1 — Shift State Record
v0.2 — Shift Handoff Record
v0.3 — Adaptive Rotation Policy
v0.4 — Multi-Wing Shift Matrix
v0.5 — Continuous Operation Receipt
```

Together, they define:

```text
State
  +
Transition
  +
Rotation decision
  +
Functional allocation
  +
Cycle audit
```

## v0.1 — Shift State Record

Version 0.1 defines the current state of an individual shift unit.

A Shift State Record describes:

* the observed system
* the participating unit
* the current shift state
* the previous state
* the planned next state
* service authority
* the current state window
* assigned duties
* prohibited duties
* load conditions
* health state
* handoff readiness
* rotation-policy reference
* audit metadata

Canonical state and authority bindings are:

| Shift state    | Service authority |
| -------------- | ----------------- |
| `ACTIVE`       | `PRIMARY`         |
| `SHADOW`       | `STANDBY`         |
| `REGENERATION` | `INTERNAL_ONLY`   |

The record establishes who currently holds responsibility and what that responsibility permits.

A conforming Shift State Record should make the following visible:

```text
Who is working?
What role are they performing?
What authority do they currently hold?
How much pressure are they carrying?
When are they expected to rotate?
Are they ready to hand off?
```

## v0.2 — Shift Handoff Record

Version 0.2 defines the transfer of responsibility between shifts.

A tri-shift handoff is not modeled as a simple two-party transfer.

It is one coordinated rotation involving three distinct units:

```text
Releasing unit:
ACTIVE → REGENERATION

Assuming unit:
SHADOW → ACTIVE

Continuity unit:
REGENERATION → SHADOW
```

### Releasing Unit

The releasing unit:

* publishes the latest trace checkpoint
* declares unfinished tasks
* declares unresolved decisions
* identifies risk flags
* freezes transferable state
* releases primary authority
* enters Regeneration duty

### Assuming Unit

The assuming unit:

* reads the latest trace checkpoint
* validates transferred context
* accepts task ownership
* confirms operational readiness
* explicitly accepts primary authority
* resumes service from the declared checkpoint

### Continuity Unit

The continuity unit:

* verifies trace integrity
* checks task ownership
* prevents dual-primary authority
* detects duplicate execution
* measures service gaps
* confirms rollback readiness
* independently audits the transition
* enters Shadow duty after Regeneration

The continuity unit is not merely a spare.

It is the independent observer that prevents the incoming and outgoing units from validating their own transition without third-party supervision.

### Authority Exclusivity

Only one unit may hold primary authority.

```text
dual_primary_allowed: false
```

The outgoing unit must release the primary authority lease before or at the moment the incoming unit acquires it.

Shadow observation may overlap with Active execution, but primary decision authority must not be duplicated.

### Transfer Payload

A Shift Handoff Record may transfer or reference:

* trace checkpoints
* active tasks
* unresolved decisions
* memory deltas
* external commitments
* tool-session state
* risk flags
* non-transferable items

Transfer does not equal acceptance.

```text
TRANSFER ≠ ACCEPTANCE
```

A handoff becomes complete only after:

* authority transfer
* mandatory verification
* explicit incoming-unit acceptance
* blocker review
* continuity confirmation
* duplicate-execution review

## v0.3 — Adaptive Rotation Policy

Version 0.3 defines why and when a rotation should occur.

A fixed schedule alone is insufficient.

A unit may need to rotate because:

* compute pressure is rising
* memory pressure is rising
* the task queue is accumulating
* error rates are increasing
* unconsolidated traces are accumulating
* unresolved context is becoming stale
* active duty has lasted too long
* fairness debt is increasing
* a hard safety trigger has fired

Version 0.3 introduces two records:

* `Adaptive Rotation Policy`
* `Rotation Evaluation Record`

The policy defines the rules.

The evaluation record preserves the evidence and resulting decision.

### Weighted Pressure

Signals are normalized and weighted.

```text
normalized signal × policy weight = score contribution
```

The total rotation score is:

```text
sum of weighted signal contributions
```

A score may include:

* compute pressure
* memory pressure
* queue pressure
* error pressure
* trace accumulation
* context staleness
* fairness debt

### Rotation Modes

The policy supports:

* `SCHEDULED`
* `ADAPTIVE`
* `HYBRID`

Scheduled rotation creates an upper duration boundary.

Adaptive rotation responds to observed pressure.

Hybrid rotation uses both.

### Decision Actions

A Rotation Evaluation Record may produce:

* `HOLD`
* `ROTATE_NOW`
* `ROTATE_AT`
* `EMERGENCY_REASSIGN`
* `ABORT_ACTIVE_WORK`

### Readiness Guards

A normal rotation should proceed only when:

```text
minimum active duration satisfied
AND
Shadow successor ready
AND
Regeneration unit complete
AND
cooldown satisfied
AND
no prohibited blocker remains
```

Pressure in the Active unit is not sufficient by itself.

A safe rotation also requires a ready successor and a ready continuity observer.

### Fairness Debt

Version 0.3 treats fairness as an operational property.

Fairness debt may increase when a unit:

* serves too many consecutive Active shifts
* exceeds its target Active-duty share
* repeatedly receives extended shifts
* remains Active despite equally capable alternatives
* carries a disproportionate share of difficult work

```text
Repeated concentration of responsibility
                ↓
         fairness debt
                ↓
       increased rotation pressure
```

This prevents a high-performing unit from becoming the invisible permanent center.

### Anti-Thrashing Protection

Adaptive rotation must not become uncontrolled oscillation.

The policy therefore supports:

* minimum Active duration
* maximum Active duration
* consecutive threshold breaches
* rolling evaluation windows
* cooldown periods
* successor-readiness thresholds
* Regeneration-completion thresholds

The goal is not to rotate as often as possible.

The goal is to rotate before responsibility concentration becomes structural exhaustion.

## v0.4 — Multi-Wing Shift Matrix

Version 0.4 connects temporal rotation with functional Multi-Wing orchestration.

The system now contains two independent dimensions.

### Functional Dimension

Examples:

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

### Temporal Dimension

```text
ACTIVE
SHADOW
REGENERATION
```

Together, they form a Multi-Wing Shift Matrix.

```text
                 ACTIVE       SHADOW       REGENERATION
Finder           Finder-A     Finder-B     Finder-C
Analyst          Analyst-A    Analyst-B    Analyst-C
Executor         Executor-A   Executor-B   Executor-C
Verifier         Verifier-A   Verifier-B   Verifier-C
Boundary         Boundary-A   Boundary-B   Boundary-C
Trace Core       Trace-A      Trace-B      Trace-C
```

Every operational role may therefore have:

* a current Active holder
* a synchronized Shadow successor
* a Regeneration member undergoing role-specific maintenance

### Rotation Domains

Version 0.4 introduces Rotation Domains.

A Rotation Domain is a related group of Wings that may rotate as one responsibility unit.

Example:

```text
Operations Domain
├─ Finder
├─ Analyst
└─ Executor

Assurance Domain
├─ Verifier
├─ Boundary
└─ Trace Core
```

This allows different functional regions to rotate at different times.

For example, the Operations Domain may rotate under high execution pressure while the Assurance Domain remains in its current allocation.

Supported domain modes include:

* `ATOMIC`
* `STAGED`

An Atomic domain rotates all declared Wings as one logical handoff.

A Staged domain may prepare individual Wing transitions separately, but must not expose an invalid mixed-authority configuration.

### Capability Compatibility

A replacement member must not merely share the same Wing label.

It must satisfy the Wing's required capabilities.

```text
Role name ≠ capability proof
```

For example, an Executor successor may be required to support:

* tool execution
* action receipt generation
* permission-bound execution

The protocol validates required capabilities separately for Active, Shadow, and Regeneration slots.

### Shadow Readiness

A Shadow Wing must be:

* technically capable
* contextually synchronized

Version 0.4 therefore distinguishes:

* `takeover_readiness_score`
* `synchronization_score`

```text
Capable but unsynchronized
        =
unsafe successor
```

### Role-Specific Regeneration

Different Wings perform different maintenance work.

Examples:

```text
Finder:
retrieval-cache cleanup
index consistency review

Analyst:
context compaction
reasoning-drift inspection

Executor:
tool-session cleanup
credential-binding review

Verifier:
validation-rule refresh
false-positive analysis

Boundary:
permission-drift inspection
policy-cache refresh

Trace Core:
trace compaction
checkpoint integrity scan
```

Regeneration is therefore defined by responsibility, not by generic inactivity.

### Provider and Region Diversity

Critical Wings may require temporal diversity across:

* providers
* regions
* infrastructure classes
* model families

Example:

```text
Active Boundary Wing       → Provider A / Region East
Shadow Boundary Wing       → Provider B / Region West
Regeneration Boundary Wing → Provider C / Region Central
```

Diversity reduces the risk that one provider failure, regional outage, policy defect, or model-specific problem disables all three temporal layers.

### Cross-Wing Dependencies

The matrix records functional dependencies such as:

```text
Finder → Analyst
Analyst → Executor
Boundary → Executor
Executor → Verifier
Executor → Trace Core
```

Dependency types may include:

* data
* control
* validation
* safety
* trace
* memory
* routing

A system may contain healthy individual Wings while still possessing a broken operational chain.

Dependency records make that failure visible.

## v0.5 — Continuous Operation Receipt

Version 0.5 closes the first protocol arc with the Continuous Operation Receipt.

The receipt binds evidence from:

* Shift State Records
* Shift Handoff Records
* Rotation Evaluation Records
* Multi-Wing Shift Matrices

It summarizes one bounded operational cycle.

```text
Cycle start
    ↓
state observation
    ↓
rotation evaluation
    ↓
handoff
    ↓
Multi-Wing reallocation
    ↓
regeneration
    ↓
cycle assessment
```

### Evidence Binding

A Continuous Operation Receipt is both:

* a cycle summary
* an evidence index

A final assessment without source-record references is not independently auditable.

### Rotation Outcome

The receipt records:

* planned rotations
* completed rotations
* aborted rotations
* emergency rotations
* domain-level participants
* authority gaps
* duplicate-primary detection
* rollback use

### Continuity Outcome

Continuous operation is evaluated through:

* availability
* total interruption duration
* maximum authority gap
* duplicate execution
* authority conflicts
* continuity service-level objectives

Service status is classified as:

* `CONTINUOUS`
* `DEGRADED`
* `INTERRUPTED`

Continuous status does not require a mathematically zero transition gap.

It requires that transition gaps remain within the declared service objective and do not cause broken authority or unsafe duplicate execution.

### Load Distribution Outcome

Version 0.5 records actual work distribution, not only shift labels.

For each unit, it may record:

* Active-duty duration
* Active-duty share
* compute-work share
* completed task count
* fairness debt before rotation
* fairness debt after rotation

```text
Equal shift labels
        ≠
equal responsibility
```

A system may rotate every eight hours while still assigning most difficult work to one group.

The receipt exposes that difference.

### Fairness Outcome

The default concentration method uses the sum of squared Active-duty shares.

```text
active-share concentration
    =
sum of squared active-duty shares
```

For three units:

```text
0.50 / 0.30 / 0.20
```

is more concentrated than:

```text
0.333 / 0.333 / 0.334
```

The receipt also records the spread between the highest and lowest Active-duty shares.

Fairness improves when concentration and spread decrease without violating capability, safety, or continuity requirements.

### Regeneration Outcome

For each Regeneration unit, the receipt may record:

* completion score
* maintenance actions completed
* maintenance actions failed
* blocker count
* return to Shadow duty

```text
Time elapsed
      ≠
Regeneration complete
```

A unit is not considered regenerated merely because its assigned period ended.

It must complete the required work and become ready to re-enter the cycle.

### Multi-Wing Outcome

The receipt records final Wing coverage.

For each Wing:

* Active member
* Shadow member
* Regeneration member
* Active health
* Shadow readiness
* Shadow synchronization
* Regeneration completion
* full-coverage state
* blocking event count

Critical-Wing coverage is evaluated separately from total coverage.

A system may have high total coverage and still fail because a critical Boundary, Executor, Verifier, or Trace Core role lacks a safe successor.

### Incident Preservation

Successful cycles do not erase minor incidents.

The receipt preserves:

* severity
* category
* blocker status
* resolution status
* evidence reference

A `PASS` receipt may contain resolved, non-blocking incidents.

### Final Assessment

The receipt status is:

* `PASS`
* `WARN`
* `FAIL`

A normal `PASS` requires:

```text
all planned rotations completed
AND
continuity SLO met
AND
no duplicate execution
AND
no authority conflict
AND
fairness improved
AND
required Regeneration completed
AND
full critical-Wing coverage
AND
no unresolved blocking incident
```

`WARN` indicates that service continuity was generally maintained, but one or more non-fatal objectives were not fully achieved.

`FAIL` indicates a structural failure involving authority, continuity, critical coverage, duplicate execution, or unresolved blockers.

### Next-Cycle Actions

The receipt may generate actions for the next operating cycle.

Examples:

* adjust a rotation threshold
* repair an underprepared Shadow Wing
* reduce fairness debt
* investigate handoff latency
* restore provider diversity
* repair critical-Wing coverage
* modify a Rotation Domain

```text
Receipt
   ↓
Next-cycle action
   ↓
Updated policy or matrix
   ↓
New cycle
```

## End-to-End Flow

A complete protocol cycle is:

```text
1. Record the current shift states
        ↓
2. Evaluate rotation pressure and readiness
        ↓
3. Decide whether to hold, rotate, or reassign
        ↓
4. Prepare a three-party handoff
        ↓
5. Release and acquire primary authority
        ↓
6. Verify continuity through the third unit
        ↓
7. Update the Multi-Wing Shift Matrix
        ↓
8. Perform role-specific Regeneration
        ↓
9. Measure continuity, fairness, and coverage
        ↓
10. Issue a Continuous Operation Receipt
```

## Design Invariants

A conforming implementation should preserve the following principles:

1. The system may remain continuously available.
2. No individual unit should remain permanently Active.
3. Active authority must not be duplicated.
4. Regeneration is an internal maintenance assignment.
5. Shadow is an observation and preparation assignment.
6. Handoff requires three distinct participants.
7. Transfer does not equal acceptance.
8. Shift transitions must be auditable.
9. Rotation decisions must preserve their evidence.
10. Required signals must be reproducible.
11. Temporary pressure spikes must not cause uncontrolled oscillation.
12. Fairness must be considered alongside efficiency.
13. Every declared Wing must have an explicit temporal allocation.
14. Capability must be verified independently of role labels.
15. Critical Wings should preserve complete three-slot coverage.
16. Actual work distribution must be measured separately from scheduled time.
17. A completed cycle must preserve incidents rather than conceal them.
18. High uptime alone must not be treated as sustainable continuity.

## Civilizational Position

Traditional load balancing asks:

```text
Where should this request run?
```

Autoscaling asks:

```text
Do we need more or fewer instances?
```

Multi-Wing orchestration asks:

```text
Which functional role should perform this work?
```

Tri-shift rotation asks:

```text
Which unit should carry this responsibility now?

Which unit should observe and prepare?

Which unit should perform internal recovery?

When should these responsibilities circulate?
```

The protocol therefore treats time, authority, recovery, observation, and fairness as first-class parts of distributed AI architecture.

```text
Spatial distribution
        ×
Temporal distribution
        =
Continuous distributed cognition
```

The objective is not to make AI sleep like a human.

The objective is to prevent one model, one agent group, one Wing, one provider, one region, or one temporal position from becoming the permanent center.

```text
The AI system remains awake.
Its responsibilities circulate.
```

## Repository Structure

```text
tri-shift-ai-rotation-protocol/
├─ README.md
├─ CHANGELOG.md
├─ requirements.txt
├─ schemas/
│  ├─ shift-state-record.schema.json
│  ├─ shift-handoff-record.schema.json
│  ├─ adaptive-rotation-policy.schema.json
│  ├─ rotation-evaluation-record.schema.json
│  ├─ multi-wing-shift-matrix.schema.json
│  └─ continuous-operation-receipt.schema.json
├─ examples/
│  ├─ shift-state-record.example.yaml
│  ├─ shift-handoff-record.example.yaml
│  ├─ adaptive-rotation-policy.example.yaml
│  ├─ rotation-evaluation-record.example.yaml
│  ├─ multi-wing-shift-matrix.example.yaml
│  └─ continuous-operation-receipt.example.yaml
├─ scripts/
│  └─ validate_examples.py
└─ .github/
   └─ workflows/
      └─ validate.yml
```

## Validation

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run validation:

```bash
python scripts/validate_examples.py
```

The validator performs two stages:

```text
1. JSON Schema validation
2. Protocol-level semantic validation
```

Semantic validation covers relationships that cannot be reliably expressed through JSON Schema alone, including:

* shift-window ordering
* authority exclusivity
* three-party handoff identity
* task-ownership transfer
* signal-weight totals
* threshold evaluation
* rotation-policy binding
* successor readiness
* fairness triggers
* Rotation Domain membership
* Wing capability coverage
* provider and region diversity
* cycle availability
* load-share totals
* fairness calculations
* Regeneration completion
* final Receipt status

Expected output:

```text
=== Tri-Shift AI Rotation Protocol Validation ===

[validate] Shift State Record
  schema : schemas/shift-state-record.schema.json
  example: examples/shift-state-record.example.yaml
[schema-ok]

[validate] Shift Handoff Record
  schema : schemas/shift-handoff-record.schema.json
  example: examples/shift-handoff-record.example.yaml
[schema-ok]

[validate] Adaptive Rotation Policy
  schema : schemas/adaptive-rotation-policy.schema.json
  example: examples/adaptive-rotation-policy.example.yaml
[schema-ok]

[validate] Rotation Evaluation Record
  schema : schemas/rotation-evaluation-record.schema.json
  example: examples/rotation-evaluation-record.example.yaml
[schema-ok]

[validate] Multi-Wing Shift Matrix
  schema : schemas/multi-wing-shift-matrix.schema.json
  example: examples/multi-wing-shift-matrix.example.yaml
[schema-ok]

[validate] Continuous Operation Receipt
  schema : schemas/continuous-operation-receipt.schema.json
  example: examples/continuous-operation-receipt.example.yaml
[schema-ok]

[semantic] Shift State Record
[semantic-ok]

[semantic] Shift Handoff Record
[semantic-ok]

[semantic] Adaptive Rotation Policy
[semantic-ok]

[semantic] Rotation Evaluation Record
[semantic-ok]

[semantic] Multi-Wing Shift Matrix
[semantic-ok]

[semantic] Continuous Operation Receipt
[semantic-ok]

All examples are valid.
```

## Scope

The first protocol arc defines:

* unit-level shift states
* three-party responsibility handoff
* adaptive rotation decisions
* Multi-Wing temporal allocation
* full-cycle continuity receipts

It does not yet define:

* cross-organization shift federation
* long-term historical fairness ledgers
* economic settlement between shift providers
* energy-price-aware geographic rotation
* human–AI mixed shift contracts
* emergency fourth-shift reserve structures
* inter-protocol royalty allocation
* global scheduling across independent AI systems

These areas are better developed as derived repositories or a second protocol arc.

## Version Status

```text
v0.1 — Shift State Record                complete
v0.2 — Shift Handoff Record              complete
v0.3 — Adaptive Rotation Policy          complete
v0.4 — Multi-Wing Shift Matrix           complete
v0.5 — Continuous Operation Receipt      complete
```

The initial specification arc is ready for:

```text
v0.5.0-candidate
```

## First-Arc Conclusion

The Tri-Shift AI Rotation Protocol does not attempt to stop AI civilization so that individual systems can rest.

It defines a different structure:

```text
Continuous service
        +
circulating authority
        +
distributed responsibility
        +
role-specific Regeneration
        +
independent verification
        +
auditable evidence
```

The result is a system that can remain continuously operational without forcing the same structure to carry the same burden indefinitely.

