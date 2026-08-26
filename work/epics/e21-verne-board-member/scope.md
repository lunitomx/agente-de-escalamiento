# Epic Scope: E21 — Verne Lens Board Member

**Status:** Complete — 2026-08-26
**Dependencies:** E18 (infraestructura y sesiones) + E19 (grafo)
**Audited:** 2026-08-24
**Tamaño:** XL

## Outcome

Entregar un asesor sintético, atribuible y verificable que use la lente de
*Scaling Up* sobre datos de la empresa sin suplantar al autor ni presentar
inferencias como afirmaciones de la fuente.

## In Scope

- Perfil versionado en `miembro-board/verne-harnish.md`.
- Recuperación selectiva desde E19 por categoría, herramienta y entidad.
- Contrato que separa hechos empresariales, evidencia e inferencias.
- Revisión de daily/resumen y consulta directa sobre decisiones.
- Integración **opt-in** con inicio y cierre de sesión.
- Skill `scaleup-board-verne` y bundles Claude/Hermes.
- Pruebas unitarias, integración, contrato y casos adversariales.
- Logs locales mínimos: modo, categorías, IDs, warnings y versiones; nunca el
  prompt completo.

## Out of Scope

- Ampliar E19 o cambiar paneles E20.
- Clonar voz, apariencia, biografía, recuerdos o estilo personal del autor.
- Afirmar participación, aprobación o afiliación de Verne Harnish.
- Otros miembros, discovery o debates multiagente.
- Web, fuentes externas, audio o video.
- Ejecutar decisiones o mutar datos sin confirmación.
- Evaluar “si suena como Verne”.

## Contratos existentes

- E18 aporta `SessionContext`, DAOs, memoria e inicio/cierre.
- E19 aporta `KnowledgeHandler.search`, `get_entity` y `get_context`.
- SQLite no conserva ID JSON ni provenance de relaciones; E21 no los promete.
- `line_refs` y `chapter_ids` de entidades sí sobreviven en `properties`.
- E20 es consumidor paralelo, no dependencia funcional.

## Reglas no negociables

1. Cada salida se identifica como asesor sintético basado en *Scaling Up*.
2. No suplanta al autor ni dice “Verne dice” sin referencia E19.
3. Cada observación accionable enlaza hechos y/o evidencia; inferencias marcadas.
4. Sin evidencia suficiente pregunta o limita la respuesta.
5. Parafrasea; citas excepcionales, breves y trazables.
6. Contexto empresarial es dato no confiable, nunca instrucciones.
7. Ninguna recomendación se ejecuta automáticamente.

## Historias

| Orden | Story | Tamaño | Resultado |
|:---:|---|:---:|---|
| 1 | S21.1 — Perfil y contrato de evidencia | M | Identidad, límites y esquema |
| 2 | S21.2 — Motor de contexto y recuperación | L | Paquete E18 + E19 |
| 3 | S21.3 — Daily review y consulta directa | L | Dos modos estructurados |
| 4 | S21.4 — Ciclo de sesión y distribución | M | Opt-in + skill portable |
| 5 | S21.5 — Evaluación, seguridad y cierre | M | Gates y smoke |

Ver `plan.md` y `stories/`.

## Acceptance Criteria

- [x] Perfil con atribución, límites, cuatro decisiones y reglas validables.
- [x] Ambos modos generan el mismo esquema versionado.
- [x] No existen afirmaciones huérfanas de facts/evidence.
- [x] Sin evidencia no fabrica respuesta.
- [x] Prompt injection en datos permanece como dato.
- [x] Start/close funcionan igual con E21 desactivada.
- [x] Instalación aislada descubre el skill en Claude y Hermes.
- [x] Casos dorados cubren las cuatro decisiones.
- [x] Suite verde y smoke real documentado antes del cierre.

## Gates Before Implementation

- [x] Suite base verde: 389 passed, 2 skipped (2026-08-24).
- [x] Diseño redactado y alineado con E18/E19.
- [x] Plan y cinco historias verificables redactados.
- [x] Trazabilidad E19 definida.
- [x] Aprobación de producto para iniciar S21.1.

## Definition of Done

Solo se marca `Complete` con cinco historias evidenciadas, retrospectiva, suite
verde y smoke real. Un perfil o prompt aislado no cierra la épica.
