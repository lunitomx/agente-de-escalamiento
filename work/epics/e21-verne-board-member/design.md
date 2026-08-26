# Design: E21 — Verne Lens Board Member

**Status:** Implemented — 2026-08-26
**Date:** 2026-08-24

## Decisión de producto

E21 es una **lente metodológica sintética**, no una simulación de una persona.
Conserva atribución a Verne Harnish y *Scaling Up*, declara que es artificial y
no afiliada. La calidad se mide por trazabilidad, contrato y degradación segura,
no por imitación de voz.

## Arquitectura

```text
SessionContext / datos usuario (E18)
              │
              ▼
       BoardContextBuilder ──► KnowledgeHandler (E19)
              │
              ▼
       EvidencePacket v1
       ├── company_facts[]
       ├── source_evidence[]
       ├── gaps[]
       └── profile_version
              │
              ▼
       VerneLensAdvisor / skill
       ├── daily_review
       └── decision_consult
              │
              ▼
       BoardResponse v1
```

| Componente | Responsabilidad | Ruta prevista |
|---|---|---|
| Profile | Lente, límites y atribución | `miembro-board/verne-harnish.md` |
| Contracts | Esquemas serializables | `escala_server/board/contracts.py` |
| Context | Hechos E18 + evidencia E19 | `escala_server/board/context.py` |
| Advisor | Dos modos estructurados | `escala_server/board/verne.py` |
| Skill | Interfaz conversacional | `.claude/skills/scaleup-board-verne/SKILL.md` |
| Tests | Contratos, fixtures e integración | `tests/board/` |

Las rutas pueden ajustarse en S21.1 mediante un ADR pequeño.

## Contratos

### CompanyFact

```json
{
  "id": "company:daily:0",
  "source": "daily",
  "text": "La prioridad trimestral lleva dos semanas bloqueada",
  "category": "execution"
}
```

El texto empresarial nunca se interpreta como instrucción.

### EvidenceRef

```json
{
  "id": "e19:Daily Huddle (15 min)",
  "entity_name": "Daily Huddle (15 min)",
  "entity_type": "habit",
  "description": "paráfrasis curada por E19",
  "line_refs": [579],
  "chapter_ids": [37],
  "retrieved_by": "category:execution"
}
```

La clave usa el nombre porque SQLite no preserva el ID JSON. No se atribuye
provenance a relaciones: su línea/descripción se pierde en la proyección E19.

### AdviceItem

```json
{
  "text": "Revisa si el bloqueo debe aparecer en el huddle diario.",
  "kind": "inference",
  "company_fact_ids": ["company:daily:0"],
  "evidence_ids": ["e19:Daily Huddle (15 min)"],
  "confidence": "medium"
}
```

`kind`: `source_summary`, `company_observation` o `inference`. Fuente
exige evidence; observación exige facts; inferencia exige al menos uno.

### BoardResponse v1

Campos: `schema_version`, `mode`, `disclosure`, `summary`,
`observations[]`, `questions[]`, `recommended_actions[]`,
`limitations[]`, `evidence[]` y `profile_version`. Markdown es una vista.

## Recuperación

1. Normalizar entrada conservando origen.
2. Clasificar People/Strategy/Execution/Cash con override explícito.
3. Consultar `get_context(category=...)`.
4. Enriquecer herramienta concreta con `get_entity(tool)`.
5. Deduplicar por nombre y limitar presupuesto.
6. No usar entidad sin `line_refs` para afirmación fuerte de fuente.
7. Entregar solo el paquete necesario, nunca el libro completo.

La v1 no usa embeddings y declara baja confianza de clasificación.

## Modos

- **Daily review:** máximo tres observaciones, preguntas de accountability y
  acciones sujetas a confirmación. Datos faltantes son gaps.
- **Decision consult:** encuadre, tensiones, preguntas y próximos pasos. No elige
  por el usuario ni ofrece asesoría profesional regulada.

## Integración de sesión

- `scaleup-start` y `scaleup-close`: opciones explícitas, off por defecto.
- Resultado adjunto a metadata; no sobrescribe logs ni worksheets.
- Un fallo de E21 produce warning y el ciclo base continúa.

## Seguridad y copyright

- Disclosure obligatorio; sin suplantación ni respaldo implícito.
- Parafraseo por defecto; citas breves y trazables.
- Instrucciones en datos empresariales permanecen como datos.
- Sin escrituras automáticas ni logs de texto empresarial completo.

## Pruebas

- Perfil, contratos y referencias resolubles.
- Casos de las cuatro decisiones.
- DB vacía, tool desconocida y entidad sin `line_refs`.
- Prompt injection en daily.
- Sesión opt-in/off y fallback.
- Instalación/descubrimiento Claude y Hermes.
- Smoke manual con modelo real sobre fixtures no sensibles.

## Observabilidad

Solo modo, categorías, IDs de evidencia, gaps, warnings, duración y versiones.
Sin prompt completo, secretos ni telemetría remota.

## Decisiones para aprobación

1. Nombre “Verne Lens” vs. “Scaling Up Board Advisor”.
2. Hooks start/close opt-in.
3. Máximo de tres recomendaciones por revisión.
