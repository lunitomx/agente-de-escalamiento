# ScaleUp Agent AI — Product Roadmap

> Inventario canónico de épicas y dirección del producto.

**Última auditoría:** 2026-08-24
**Estado auditado:** main en 67c3d0c (epic/e20-complete)
**Siguiente número disponible:** E22

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
| E9 — Value-Add | Export, pulse, dashboard y summary | ✅ Complete — follow-up | 4/4 al cierre. coaching/summary/ fue retirado en E13 y requiere port si se desea restaurar. |
| E10 — Cross-Platform Distribution | Engines e instalador Claude/Hermes | ✅ Complete — accepted follow-ups | 9/9; no se verificó el flujo completo desde proyecto limpio ni el remapeo real de Hermes. |
| E11 — Agente de Escalamiento | Repositorio público anonimizado | ✅ Complete | 6/6; retrospectiva registra clon e instalación verificados. |
| E12 — Codex & Auto-Update | Compatibilidad y actualización | ❌ Cancelled | Absorbida por E11; cierre 6bfcaac. |
| E13 — Auditoría y Cierre | Sanear cierres, tests y fuentes duplicadas | ✅ Complete | 9/9; 139 tests en el cierre histórico. |
| E14 — Cash Dashboards | 4 dashboards Cash | ✅ Complete | 4/4. |
| E15 — Strategy Dashboards | 5 dashboards Strategy | ✅ Complete | 5/5. |
| E16 — People Dashboards | 6 dashboards People | ✅ Complete | 6/6. |
| E17 — Execution Dashboards | 7 dashboards Execution | ✅ Complete | 7/7. |
| E18 — Escala Server | Servidor, dashboards, SQLite y memoria | ✅ Complete | 12/12; close 2a63e09. |
| E19 — Book Ingestion | Parser, grafo y API de conocimiento | ✅ Complete | 5/5; S19.3 absorbida por S19.2; 42 entidades, 59 relaciones y 406 capítulos. |
| E20 — Contextual Skills | Grafo → dashboards y coaching | ✅ Complete | 4/4; close 67c3d0c; tag epic/e20-complete. |
| E21 — Verne Board Member | Primer miembro del board sintético | 📝 Draft | Única épica pendiente formal; todavía sin diseño, plan ni historias. |

### Resumen

- 17 épicas completas: E1, E2, E3, E6–E11 y E13–E20.
- 1 épica cancelada: E12.
- 2 borradores históricos retirados/sustituidos: E4 y E5.
- 1 épica en borrador: E21.
- No existe una E22 formalizada.

## Secuencia actual

    E18 Escala Server ──► E19 Book Ingestion ──► E20 Contextual Skills
           DONE                    DONE                    DONE
                                                              │
                                                              ▼
                                                  E21 Verne Board Member
                                                            DRAFT

E21 depende funcionalmente de E19 y de la infraestructura de E18. No depende de
E20 para comenzar; E20 es una integración consumidora paralela del conocimiento.

## Próximo trabajo recomendado

### P0 — Restaurar estado verde antes de abrir E21

La auditoría del 2026-08-24 ejecutó la suite con Python 3.12:

- 380 passed
- 2 failed
- 2 skipped
- 1 warning

Fallos actuales:

1. _parse_simple_yaml() no construye listas YAML de nivel raíz.
2. read_yaml_file() no interpreta correctamente pulses: con elementos de lista
   en .scaleup/my-company/pulse-history.yaml.

### P1 — Preparar E21

1. Revisar el brief y scope con las dependencias ya reconciliadas.
2. Ejecutar diseño y plan formal.
3. Dividir el tamaño XL en historias verificables.
4. Definir pruebas de fidelidad al libro sin imitación personal ni citas extensas.

## Deuda técnica y de producto no asignada

| Deuda | Origen | Estado | Condición de promoción |
|-------|--------|--------|------------------------|
| Suite roja: parser YAML | E18 / auditoría 2026-08-24 | Open — P0 | Corregir antes de iniciar implementación nueva. |
| Instalación E2E desde proyecto limpio | E4/E10/E13 | Open — P1 | Promover a E22 si requiere más que una historia acotada. |
| Remapeo y prueba real de Hermes | E10 | Open — P1 | Cuando Hermes sea plataforma soportada, no solo destino de copia. |
| Restaurar coaching/summary/ | E9/E13 | Open — P2 | Cuando se requiera nuevamente resumen automático de sesión. |
| Documentar formalmente el esquema E19 | E19 | Open — P2 | Antes de extender el grafo con nuevas fuentes. |
| Integrar Escala Server con el instalador | E18 | Open — P2 | Antes de distribuir el servidor fuera del repo. |
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
| Regresiones de migración | Restaurar suite verde y añadir fixtures YAML de listas anidadas. |

---

*Creado: 2026-03-17 | Auditado: 2026-08-24 | Estado: Active*
