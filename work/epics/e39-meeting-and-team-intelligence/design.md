# E39: Meeting and Team Intelligence — Design

## Gemba findings

- `escala_server/workspace/ingestion.py` ya expone `SourceIdentity`, `build_source_identity` y perfiles de texto; E39 debe consumirlos, no crear otra identidad.
- `escala_server/workspace/inbox.py` escanea solo entradas directas, guarda un ledger local bajo `data_root` y no sigue symlinks ni mueve originales; S39.1 puede reutilizarlo para idempotencia.
- `escala_server/workspace/authority.py` es la autoridad para `installer_machine`, `ordinary_filesystem_documents_only` y `authoritative_sqlite_sync=forbidden`; S39.4 debe invocarla.
- E38 usa modelos Pydantic estrictos, receipts redacted y artefactos deterministas; E39 seguirá ese patrón.
- No existe módulo previo de meeting intelligence en `escala_server`; el seam es net-new y no deja V1 huérfano.

## Approach

Crear `escala_server/meetings/` como una capa local de cuatro piezas pequeñas: intake/ledger, parser de contexto, extracción temporal y reportes/agenda. Los módulos intercambian modelos Pydantic inmutables; los reportes solo escriben bajo `data_root`. El parser será deliberadamente heurístico y bilingüe (español/inglés) con líneas como unidad de evidencia; no intentará resolver lenguaje universal.

### Components

- `escala_server/meetings/models.py` — contratos cerrados: provenance, context, evidence, facts, rhythm, trends, review, schedule.
- `escala_server/meetings/intake.py` — consume `WorkspaceConfig`, `build_source_identity`, escanea `.txt/.md/.transcript`, y persiste ledger JSON local idempotente.
- `escala_server/meetings/extraction.py` — detecta contexto y hechos por reglas, con `unresolved` y confidence.
- `escala_server/meetings/analysis.py` — evalúa ritmo, tendencias, salud y preguntas sin inventar negativos.
- `escala_server/meetings/report.py` — genera Markdown/HTML/JSON locales y agenda declarativa; escapa HTML y redacts receipts.
- `tests/test_e39_meeting_intelligence.py` — fixture sintético Nopal Foods y negativos.
- `validators/e39_gates.py` — siete gates que exigen qualification y tests focalizados.
- `scripts/qualify_e39.py` — qualification sintética y receipts exactos.

## Key decisions

### D1 — JSON local para derivados, no SQLite compartida

El ledger de source identities y los hechos derivados viven bajo `data_root` en JSON atómico. Esto evita migrar el esquema SQLite y hace visible la prohibición de sincronización de autoridad; la carpeta exchange nunca recibe estado canónico.

### D2 — Evidencia por línea, no copia de transcript

Cada hecho referencia `source_id`, ruta relativa, líneas y `evidence_sha256`. El modelo puede mostrar preguntas y confianza sin filtrar texto privado a receipts; el transcript original permanece inmutable en exchange.

### D3 — Ausencia es estado de evidencia

El ritmo y la revisión distinguen `evidence_present`, `evidence_missing`, `unresolved` y `supported`. No se asigna score negativo ni se infiere enojo, culpa o bajo desempeño por no recibir un archivo.

### D4 — Reglas declarativas y agenda pull-local

La agenda es un manifiesto local con frecuencia y último run; no se crea un daemon, cron remoto ni integración cloud. El director puede ejecutar `run_daily_review` cuando lo decida y exportar archivos a una carpeta ordinaria.

## Data flow

`exchange file → E37 SourceIdentity → local meeting ledger → context/facts → cross-meeting analysis → local report`

El único write path autoritativo es `data_root`; `exchange_root` se lee y nunca recibe SQLite o derivados. `WorkspaceConfig` se valida antes de cualquier escritura.

## Complexity and drift

Complejidad total: moderada/alta por cuatro contratos conectados y reglas temporales. No hay `governance/drift-hotspots.json`; AG2 (clone amplification) se mitiga reutilizando E37, y AG4 se limita a una nueva carpeta con API pública única. No se introduce dependencia externa: solo stdlib y Pydantic ya presentes.

## Testing strategy

- Unit: source identity, idempotency, context ambiguity, evidence/confidence, rhythm missing state, trend classification.
- Integration: synthetic daily/weekly transcripts through one local WorkspaceConfig and report artifact.
- Negative: duplicate source, ambiguous context, missing transcript, unresolved decisions, exchange containing SQLite.
- Determinism/redaction: repeat runs produce identical IDs/reports and never expose machine paths or source text in receipts.

## Out of scope and follow-ups

DISC, cockpit, psychological inference and product catalog remain E40/E42. Audio/transcription and native Windows execution remain E41/E42.
