# Epic Retrospective: E41 Local Installation and Lifecycle

**Completed:** 2026-07-22  
**Stories:** 4 delivered  
**Requirements:** 7/7 proved by local receipts

## Summary

E41 convierte el runtime de ESCALA en un producto instalable y mantenible en
la máquina del empresario. El paquete excluye la disposición de desarrollo,
valida la frontera de autoridad antes de escribir, mantiene el exchange como
documentos, y deja evidencia de backup, actualización, rollback y scheduling.

## Metrics

| Metric | Value |
|---|---:|
| Focused lifecycle tests | 12 |
| Focused gate tests | 2 |
| Requirements proved | 7/7 |
| Platforms qualified | macOS, Windows (platform simulation) |
| Hosted/network runtime dependencies | 0 |

## Scope audit

| Commitment | Evidence | Result |
|---|---|---|
| Install without repository layout | `installer.py`, REQ-E41-001/002 | Fulfilled |
| Local health/version/stop | `runtime.py`, REQ-E41-003 | Fulfilled |
| Backup/migration/update/rollback | `updates.py`, REQ-E41-004/005 | Fulfilled |
| Optional document exchange | authority integration, REQ-E41-006 | Fulfilled |
| Native offline scheduling | `scheduler.py`, REQ-E41-007 | Fulfilled |

## What went well

- Reusing E37 authority made the SQLite/exchange boundary executable instead of documentary.
- Hash verification and pre-write backups make update failure observable and recoverable.
- The qualification deliberately exercises both platform contracts and negative cases.

## What could be improved

- Real hardware acceptance on a clean macOS and Windows machine remains an E42/HITL release gate.
- Code signing/notarization and a signed public artifact remain intentionally unauthorized.
- A future UI may call these local contracts, but no hosted UI was added here.

## Patterns

- Authority before side effect.
- Evidence receipt before ledger proof.
- Safe-stop is preferable to partially applied migration.

## Release posture

No push, publication, signing or external tracker mutation was performed. The
tag is local only and legal/publication review remains required.
