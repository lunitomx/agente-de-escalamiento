# ScaleUp Agent AI — Product Roadmap

> Inventario canónico de épicas y dirección del producto.

**Última auditoría:** 2026-08-26
**Estado auditado:** main; E20 cerrada y E21/E22 planificadas
**Siguiente número disponible:** E23

## Visión

Convertir Scaling Up en un coach AI local-first con memoria, conocimiento
estructurado, herramientas visuales y acompañamiento accionable en People,
Strategy, Execution y Cash.

El producto evolucionó desde skills locales hasta incluir un coaching engine
portable, 22 dashboards, un servidor HTTP local, persistencia SQLite y un grafo
de conocimiento derivado del libro.

## Reglas del inventario

1. Los identificadores históricos no se renumeran ni se reutilizan.
2. Un cierre se acredita con retrospectiva y evidencia en Git; un checkbox
   desactualizado no reabre por sí solo una épica.
3. Retired / Superseded significa que el borrador dejó de ser la unidad de
   ejecución. No significa que todos sus criterios se hayan cumplido.
4. Las deudas residuales se registran por separado. Si se promueven a una nueva
   épica, deben comenzar en E22.

## Auditoría de numeración

E1–E5 fueron registrados en el backlog inicial del commit a9c93f8:

| ID | Registro original | Resultado de la auditoría |
|----|-------------------|----------------------------|
| E1 | OCR Pipeline | Completa antes de E3. Solo conserva evidencia histórica de gobernanza; sus salidas sobreviven en las fuentes parseadas. |
| E2 | Knowledge Base | Completa antes de E3. Su implementación fue ampliada y parcialmente reemplazada por E6 y E19. |
| E3 | Agent Framework | Primera épica con directorio propio en work/epics/; completa. |
| E4 | Validation | Borrador histórico. Nunca tuvo directorio, historias ejecutadas ni cierre propio. Retirada/sustituida por validaciones distribuidas en E13, E19 y E20; quedan deudas E2E. |
| E5 | Distribution | Borrador histórico. Nunca tuvo directorio, historias ejecutadas ni cierre propio. Retirada/sustituida por E10 y E11; quedan validaciones de instalación/release. |

La ausencia de carpetas E1, E2, E4 y E5 no representa números disponibles.
Todos forman parte de la historia del producto.

## Inventario canónico

| Epic | Objetivo | Estado canónico | Evidencia / observaciones |
|------|----------|------------------|--------------------------|
| E1 — OCR Pipeline | Extraer el libro a texto/markdown | ✅ Complete — legacy | Backlog inicial: done; sin artefacto work/epics/. |
| E2 — Knowledge Base | Estructurar contenido por las 4 decisiones | ✅ Complete — legacy | Backlog inicial: done; evolucionó hacia E6/E19. |
| E3 — Agent Framework | Repo instalable y skills invocables | ✅ Complete | 5/5; close 0bbc74d; tag epic/e3-complete. |
| E4 — Validation | Validación E2E del producto completo | ⏹ Retired / Superseded | Borrador sin ejecución propia. Cobertura parcial en E13/E19/E20. |
| E5 — Distribution | Publicación y distribución | ⏹ Retired / Superseded | Borrador sin ejecución propia. Sustituida por E10/E11. |
| E6 — Knowledge Ontology | Ontología y retrieval determinístico | ✅ Complete | 7/7; ~70 nodos, 301 edges y **15** worksheets registrados. |
| E7 — Agent Intelligence | Memoria, sesiones, tareas y routing | ✅ Complete | 6/6; cierre formal 7630a5a. |
| E8 — Coaching Engine | Coaching Python portable | ✅ Complete | 6/6; opera sobre los 15 worksheets registrados actualmente. |
| E9 — Value-Add | Export, pulse, dashboard y summary | ✅ Complete | 4/4; coaching/summary/ restaurado en la ruta canónica, con CLI, idempotencia y distribución. |
| E10 — Cross-Platform Distribution | Engines e instalador Claude/Hermes | ✅ Complete — accepted follow-up | 9/9; instalación aislada, adapters, flujo determinístico y descubrimiento Hermes verificados; falta smoke conversacional con proveedor real. |
| E11 — Agente de Escalamiento | Repositorio público anonimizado | ✅ Complete | 6/6; retrospectiva registra clon e instalación verificados. |
| E12 — Codex & Auto-Update | Compatibilidad y actualización | ❌ Cancelled | Absorbida por E11; cierre 6bfcaac. |
| E13 — Auditoría y Cierre | Sanear cierres, tests y fuentes duplicadas | ✅ Complete | 9/9; 139 tests en el cierre histórico. |
| E14 — Cash Dashboards | 4 dashboards Cash | ✅ Complete | 4/4. |
| E15 — Strategy Dashboards | 5 dashboards Strategy | ✅ Complete | 5/5. |
| E16 — People Dashboards | 6 dashboards People | ✅ Complete | 6/6. |
| E17 — Execution Dashboards | 7 dashboards Execution | ✅ Complete | 7/7. |
| E18 — Escala Server | Servidor, dashboards, SQLite y memoria | ✅ Complete | 12/12; close 2a63e09. |
| E19 — Book Ingestion | Parser, grafo y API de conocimiento | ✅ Complete | 5/5; 42 entidades, 59 relaciones, 406 capítulos y esquema formal documentado. |
| E20 — Contextual Skills | Grafo → dashboards y coaching | ✅ Complete | 4/4; close 67c3d0c; tag epic/e20-complete. |
| E21 — Verne Lens Board Member | Primer asesor del board sintético | 📐 Planned — approval pending | Diseño, plan, trazabilidad y 5 stories listos; sin implementación. |
| E22 — Memoria Empresarial Integrada | Conectar SQLite, hechos, grafo y sesiones de E18 al producto instalado | 📐 Planned — design gate | Brief/scope creados tras diagnóstico RaiSE 2026-08-26; no implementación sin ADR de fuente única, migración y privacidad. |

### Resumen

- 17 épicas completas: E1, E2, E3, E6–E11 y E13–E20.
- 1 épica cancelada: E12.
- 2 borradores históricos retirados/sustituidos: E4 y E5.
- 2 épicas planificadas: E21 (board sintético) y E22 (memoria empresarial integrada).
- No existe una E23 formalizada.

## Secuencia actual

    E18 Escala Server ──► E19 Book Ingestion ──► E20 Contextual Skills
           DONE                    DONE                    DONE
                                                              │
                                                              ▼
                                                  E21 Verne Lens Board Member
                                                  PLANNED / APPROVAL GATE

E21 depende funcionalmente de E19 y de la infraestructura de E18. No depende de
E20 para comenzar; E20 es una integración consumidora paralela del conocimiento.

## Próximo trabajo recomendado

### P0 — E22: Integrar memoria empresarial al producto instalado

La RC actual acreditó recorridos naturales completos en Claude Code y Codex
(404 passed, 2 skipped). El diagnóstico de 2026-08-26 confirmó que el runtime
SQLite/memoria de E18 no se instala ni se invoca desde la puerta pública. E22
debe resolver esa separación antes de presentar ScaleUp como memoria empresarial neurosimbólica.

### P1 — Aprobar e implementar E21

1. Aprobar el nombre visible y disclosure del asesor sintético.
2. Confirmar hooks start/close opt-in y máximo de tres recomendaciones.
3. Implementar S21.1–S21.5 en el orden documentado.
4. Cerrar solo con trazabilidad automática y smoke conversacional real.

## Deuda técnica y de producto no asignada

| Deuda | Origen | Estado | Condición de promoción |
|-------|--------|--------|------------------------|
| Smoke conversacional desde proyecto limpio | E4/E10/E13 | Open — P0 | Autorizar consumo de modelo y ejecutar Claude/Hermes; la aceptación determinística ya está automatizada. |
| Bootstrap de Hermes | E10 / entorno | Open — P0 | Corregir lectura de `/usr/local/lib/hermes-agent/.env` antes del smoke. |
| Integrar Escala Server con el instalador | E18 | Promovida a E22 | E22 define fuente única, migración y E2E antes de distribuirla. |
| Compatibilidad Python declarada | E18/E20 | Open — P2 | Definir y probar una versión mínima única. |
| Release verificable del repo fuente | E5 | Open — P2 | Si se publica este repo; .scaleup/VERSION es 1.0.0, pero no existe tag v1.0.0 aquí. |
| Rama origin/story/s6.1/ontology-schema | Higiene Git | Open — P3 | Eliminar tras confirmar que está fusionada y no se usa. |

Las ideas condicionadas que no son deuda comprometida viven en dev/parking-lot.md.

## Riesgos vigentes

| Riesgo | Mitigación |
|--------|------------|
| Roadmap y scopes divergen del código | Esta tabla es el inventario canónico; auditar al cerrar cada épica. |
| Declarar completitud por checkbox sin evidencia | Priorizar retrospectiva, código, pruebas y commits de cierre. |
| Contexto excesivo del grafo | Carga selectiva por herramienta/decisión; no cargar el libro completo. |
| Respuestas de E21 no fundamentadas | Recuperación obligatoria desde E19 y pruebas de trazabilidad. |
| Regresiones de migración | Suite verde y fixtures YAML de listas anidadas; conservarlos en el gate completo. |

---

*Creado: 2026-03-17 | Auditado: 2026-08-24 | Estado: Active*
