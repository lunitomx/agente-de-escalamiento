# E41 Master Acceptance Receipt

- status: pass
- platform matrix: macos, windows
- requirements_proved: REQ-E41-001 … REQ-E41-007

## Proof

- REQ-E41-001: A clean macOS target installed the archive into app/data roots without repository layout or network access.
- REQ-E41-002: A clean Windows target used the same manifest capability set with platform-specific recorded evidence.
- REQ-E41-003: Both simulated platforms started and stopped a local marker runtime reporting health, version and data_root.
- REQ-E41-004: Schema migration created a local backup and interrupted migration returned safe_stop with rollback_available.
- REQ-E41-005: A hash-verified update preserved company state, version provenance and a tested rollback receipt; tampering failed before writes.
- REQ-E41-006: An optional exchange root was configured as document-only while data_root and SQLite remained outside it.
- REQ-E41-007: macOS/Windows install, runtime, offline schedule, permissions/authority, update, rollback, corruption and publication-boundary checks passed.

## Negative matrix

- cross-platform bundle mismatch rejected
- synchronized SQLite authority rejected
- tampered update rejected before writes
- interrupted migration safe-stopped with recoverable backup
- native schedules contain no network action

## Authority

- runtime/data authority: installer_machine
- team exchange: ordinary_filesystem_documents_only
- authoritative SQLite sync: forbidden
