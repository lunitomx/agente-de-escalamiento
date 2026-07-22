# Epic Retrospective: E37 Local Workspace & Flexible Ingestion

**Completed:** 2026-07-22
**Duration:** same day; story implementation span was approximately 44 minutes
from the first S37.1 implementation commit through S37.3 completion
**Stories:** 3 stories delivered

## Summary

E37 entregó la frontera local que faltaba para que ESCALA reciba archivos del
empresario sin convertirlos en un requisito de plantilla ni en una integración
cloud. El runtime, SQLite y los ledgers autoritativos quedan en la máquina del
instalador; una carpeta ordinaria —también una carpeta ya sincronizada por
Drive/OneDrive— funciona únicamente como intercambio de documentos.

La épica quedó formalmente probada: `REQ-E37-001`…`REQ-E37-007` tienen artefacto,
receipt hash-bound y gate específico; el readiness del ledger devuelve `proved`
7/7. E38-E40 pueden consumir perfiles y receipts sin duplicar el contrato de
autoridad.

## Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Stories Delivered | 3 | S37.1, S37.2, S37.3; todas integradas en `main` |
| Story Points | N/A | El scope usó tamaños M/L/M, sin calibración SP confiable |
| Tests Added | 39 focused assertions in close run | 9 gate-contract tests + 30 workspace tests; full suite gate passed |
| Average Velocity | N/A | No baseline comparable; se conservaron tiempos observados |
| Calendar Days | 1 | 2026-07-22 |

### Story Breakdown

| Story | Size | Actual | Key Learning |
|-------|:----:|:------:|--------------|
| S37.1 | M | 17m02s | La containment debe resolver symlinks hasta el boundary semántico, no hasta `/`. |
| S37.2 | L | 17m59s | Una identidad por procedencia relativa + bytes permite reruns honestos sin rutas de máquina. |
| S37.3 | M | ~9m53s | Un ledger local fuera del exchange hace posible `duplicate` read-only y cuarentena no destructiva. |

## What Went Well

- TDD mantuvo visibles los límites: autoridad, formatos, ambigüedad, identidad,
  idempotencia, redacción y no mutación.
- La qualification temporal real encontró y corrigió el límite de tamaño de
  S37.3 antes de aceptar la evidencia.
- La solución no añadió OAuth, APIs de Drive/OneDrive, base de datos cloud,
  watcher, worker hospedado ni movimiento destructivo de documentos.
- Se resolvió el defecto de gobernanza descubierto al cierre: los siete
  `gate-req-e37-*` ahora están registrados como entry points instalables y
  ejercen pruebas focalizadas.
- El master acceptance ledger distingue evidencia de story de proof formal y
  ahora refleja 7 requisitos proved, no una promesa basada en tests solamente.

## What Could Be Improved

- Los gates de requisito debieron existir desde E37 design/plan; su ausencia
  retrasó el cierre aunque la implementación ya estaba lista.
- El cierre Windows sigue siendo revisión de contrato/rutas desde macOS; una
  ejecución nativa Windows debe quedar en E41/E42 y no se debe inferir aquí.
- La registry XLSX es deliberadamente mínima y PDF permanece
  `provider_unavailable`; E38 debe ampliar capacidades solo con fixtures reales
  y límites explícitos.
- Los learning records formales de RaiSE para design/plan/implement no están
  presentes en este checkout; se reportó el gap en las retrospectivas y no se
  fabricaron métricas de aceptación.

## Patterns Discovered

| ID | Pattern | Context |
|----|---------|---------|
| PAT-L-1302 | Resolver containment antes de abrir SQLite y detener la inspección en el boundary declarado. | Workspace y symlink guard. |
| PAT-L-1303 | Separar evidencia de story de proof del ledger maestro. | Receipts hash-bound de E37. |
| PAT-L-1304 | Identidad por procedencia relativa + bytes, con receipts estructurales redacted. | Ingestión y rerun. |
| PAT-L-1305 | Outcomes explícitos cuando un adapter no puede interpretar una fuente. | PDF, corruptos y formatos desconocidos. |
| PAT-L-1306 | Ledger de idempotencia fuera del exchange: primera disposición, duplicate read-only y nueva identidad por bytes. | Inbox diario. |
| PAT-L-6 | Writer/validator local con persistencia atómica y contratos cerrados. | Ledger y reportes del inbox. |

## Process Insights

- “Historia cerrada” y “requisito probado” son estados diferentes; la épica
  necesita ambos antes de cambiar el scope a `complete`.
- La revisión item-by-item del scope evitó confundir una carpeta sincronizada
  con una API cloud y confirmó que no hubo eliminación o reemplazo oculto.
- Los gates específicos deben ser discoverable por `rai gate list` antes de
  preparar receipts; un nombre declarado en YAML no basta.
- El flujo local-only es más simple y verificable cuando el intercambio se
  trata como filesystem ordinario y el estado autoritativo tiene una raíz
  separada.

## Artifacts

- **Scope:** `work/epics/e37-local-workspace-flexible-ingestion/scope.md`
- **Brief:** `work/epics/e37-local-workspace-flexible-ingestion/brief.md`
- **Design/ADR:** `design.md`, `adr-local-authority-and-inbox.md`
- **Story evidence:** `stories/s37.1-evidence/`, `stories/s37.2-evidence/`,
  `stories/s37.3-evidence/`
- **Master proof:** `evidence/REQ-E37-00{1..7}.{json,receipt.json}` y
  `evidence/master-acceptance-e37.{json,md}`
- **Gate implementation:** `validators/e37_gates.py`, entry points en
  `pyproject.toml`, tests en `tests/test_e37_gates.py`
- **Tests:** 39 focused tests passed; `gate-tests` full suite passed.

## Acceptance and Boundary

- Epic close gates: `gate-epic-close-drift` y los siete `gate-req-e37-*` PASS.
- Core quality gates: `gate-format`, `gate-lint`, `gate-tests`, `gate-types`
  PASS.
- E37 master readiness: `proved_count=7`, `unproved_count=0` para el filtro
  E37; el mission ledger completo sigue en `7/42`.
- Plataforma observada: macOS. Windows queda como revisión de contrato y
  rutas compatible con el alcance; no se afirma una corrida nativa no hecha.
- Publicación/push: no ejecutados. El remoto queda sin cambios por diseño.
- Backlog/docs remoto: omitidos; no hay adapter configurado.

## Next Steps

- E38 consume `SourceProfile`, identidades y receipts para reconstrucción
  financiera; debe mantener la separación entre inferencia y hecho confirmado.
- E39 añade revisión de dailies/weeklies y reportes diarios sobre el mismo
  inbox, sin crear un worker hospedado.
- E40 construye diagnóstico, cockpit visual y coaching sobre evidencia local.
- E41/E42 deben probar instalación nativa, calificación completa, catálogo
  funcional y el PDF español solicitado; E37 no los anticipa.
