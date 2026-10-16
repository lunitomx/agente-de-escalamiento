# E41 Master Acceptance Receipt

- status: pass
- platform matrix: macos, windows
- requirements_proved: REQ-E41-001 … REQ-E41-007

## Proof

- REQ-E41-001: A clean macOS target prepared local install/data roots, version marker and SQLite without network access; the owner installs with the documented one-line flow (instalar.sh: git clone into ~/ESCALA, then install.sh --platform claude --with-specialists; the same line updates with git pull --ff-only). The E41 zip archive was retired in S86.35.
- REQ-E41-002: A clean Windows target prepared the same local install/data roots, version marker and SQLite with platform-specific recorded evidence. There is no native Windows install: instalar.sh stops and points the owner to WSL2, where the same line installs ESCALA.
- REQ-E41-003: Both simulated platforms started and stopped a local marker runtime reporting health, version and data_root.
- REQ-E41-004: Schema migration created a local backup and interrupted migration returned safe_stop with rollback_available.
- REQ-E41-005: A hash-verified update preserved company state, version provenance and a tested rollback receipt; tampering failed before writes.
- REQ-E41-006: An optional exchange root was configured as document-only while data_root and SQLite remained outside it.
- REQ-E41-007: macOS/Windows local preparation, runtime, offline schedule, permissions/authority, update, rollback, tampering and publication-boundary checks passed.

## Negative matrix

- synchronized SQLite authority rejected
- tampered update rejected before writes
- interrupted migration safe-stopped with recoverable backup
- native schedules contain no network action

## Authority

- runtime/data authority: installer_machine
- team exchange: ordinary_filesystem_documents_only
- authoritative SQLite sync: forbidden
