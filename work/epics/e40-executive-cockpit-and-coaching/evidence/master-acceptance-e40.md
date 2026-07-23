# E40 Master Acceptance Receipt

- status: pass
- fixture: synthetic-nopal-foods
- requirements_proved: REQ-E40-001 … REQ-E40-008

## Proof

- REQ-E40-001: Nopal Foods profile validated with five required facts and no unresolved fields.
- REQ-E40-002: People, Strategy, Execution and Cash each received a deterministic attributed 0-100 assessment.
- REQ-E40-003: Cash was selected as supported pain and drilled to cash-001, freshness, blocker and next action.
- REQ-E40-004: Partial OPSP retained purpose/BHAG and exposed unresolved critical sections; complete plan remained owner-supplied.
- REQ-E40-005: Explicit Cash routed to /escala-cash; People without evidence returned supported=false and a question.
- REQ-E40-006: Goals, priority, task, owner, due dates, progress and session continuity round-tripped through local execution.json.
- REQ-E40-007: Cockpit HTML/JSON were written below data_root with relative artifact paths and no exchange writes.
- REQ-E40-008: Guidance preserved facts, inference and unknown CCC while asking a material question; invalid authority failed closed.

## Negative matrix

- missing profile fields remain unresolved
- missing decision evidence is evidence-limited
- HTML values are escaped
- exchange SQLite is rejected before writes
- corrupt execution state is rejected
- unsupported route asks a question instead of claiming analysis

## Authority

- runtime/data authority: installer_machine
- team exchange: ordinary_filesystem_documents_only
- authoritative SQLite sync: forbidden
