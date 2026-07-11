# Changelog

All notable changes to the Tri-Shift AI Rotation Protocol are documented in this file.

The format is based on Keep a Changelog, and the project uses semantic versioning where applicable.

## [Unreleased]

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
  * multi-wing groups
  * service clusters
  * hybrid units
* Added state-window and sequence-number fields.
* Added responsibility and prohibited-duty records.
* Added compute, memory, queue, error-rate, capacity, and health snapshots.
* Added preliminary handoff readiness and trace-checkpoint references.
* Added scheduled, adaptive, and hybrid rotation-policy declarations.
* Added immutable audit metadata.
* Added a valid YAML example.
* Added Python-based JSON Schema validation.
* Added GitHub Actions validation workflow.

### Design Decision

Version 0.1 adopts:

```text
ACTIVE → REGENERATION → SHADOW → ACTIVE
```

rather than:

```text
ACTIVE → SHADOW → REGENERATION → ACTIVE
```

This ensures that a unit undergoes internal maintenance immediately after primary service and enters shadow synchronization immediately before returning to active authority.

### Scope Limitations

Version 0.1 does not yet define:

* detailed handoff payloads
* pending-task transfer
* trace-delta transfer
* emergency takeover
* adaptive trigger evaluation
* multi-wing shift allocation
* cluster-wide rotation validation
* continuous-operation receipts
