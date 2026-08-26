# Epic Scope: E22 — Memoria Empresarial Integrada

**Status:** Designed — implementation gated
**Dependencies:** E10 (distribución), E18 (SQLite, memoria, grafo y sesiones)
**Audited:** 2026-08-26
**Tamaño:** L

## Outcome

Entregar un ScaleUp local-first con una sola memoria empresarial por proyecto.
La conversación pública debe recuperar contexto relevante al empezar y guardar
hechos, decisiones y aprendizajes confirmados al cerrar, sin exponer comandos,
skills, rutas ni la arquitectura al empresario.

## In Scope

- Contrato versionado de memoria: hechos, decisiones, aprendizajes, entidades,
  relaciones, fuente, fecha, confianza, conflicto y confirmación.
- Decisión explícita de fuente de verdad SQLite y compatibilidad/migración de
  los YAML actuales: perfil, conversación, plan y worksheets.
- Distribución del runtime necesario de E18 desde install.sh para Claude, Codex
  y Hermes, sin servicio externo ni dependencia de plugin.
- Base SQLite local por proyecto, con creación, health check, backup/restore y
  migración idempotente.
- Inicio de sesión: recuperar perfil, últimos cambios y facts relevantes con
  degradación segura si aún no hay datos.
- Cierre/pausa de sesión: proponer y guardar sólo hechos, decisiones o patrones
  autorizados por la persona; registrar proveniencia.
- Integración de inicio/cierre y recuperación en el front door público sin
  romper onboarding, diagnóstico, plan ni progreso actuales.
- Tests unitarios, de migración, integración y cliente real desde instalación
  limpia; actualización de documentación de privacidad y rollback.

## Out of Scope

- Cloud, sincronización entre dispositivos, multiusuario, CRM o telemetría.
- Plugin Holographic, vector database, embeddings o búsqueda semántica neural
  hasta que una evaluación pruebe que SQLite/índices deterministas no bastan.
- Guardar automáticamente inferencias del modelo como hechos de empresa.
- Rediseñar todos los dashboards E14–E17 antes de cerrar la fuente única.
- Board sintético E21, fuentes nuevas de conocimiento o recomendaciones
  financieras/legales.

## Reglas no negociables

1. Los datos empresariales permanecen locales y visibles/exportables para la
   empresa.
2. Ninguna inferencia se convierte en hecho sin fuente y confirmación definida.
3. SQLite no puede coexistir indefinidamente como copia divergente del YAML.
4. Migración, actualización, desinstalación y rollback deben preservar datos.
5. La persona sigue usando lenguaje natural; la memoria no añade comandos ni
   jerga al recorrido público.
6. Sin memoria disponible, ScaleUp degrada al flujo actual sin bloquear a la
   persona ni inventar contexto.

## Historias propuestas

| Orden | Story | Tamaño | Resultado |
|:---:|---|:---:|---|
| 1 | S22.1 — Contrato y ADR de memoria | M | Esquemas, privacidad, confirmación y fuente única definidos. |
| 2 | S22.2 — Runtime, instalación y ciclo SQLite | L | E18 se distribuye, crea/valida base por proyecto y permite rollback. |
| 3 | S22.3 — Migración YAML idempotente | L | Perfil, diagnóstico, plan y worksheets migran sin pérdida ni duplicados. |
| 4 | S22.4 — Inicio y recuperación contextual | M | Sesión nueva recupera facts, cambios y foco relevante. |
| 5 | S22.5 — Cierre, hechos y patrones confirmados | L | Decisiones/aprendizajes con fuente, confianza y confirmación. |
| 6 | S22.6 — Front door y continuidad natural | M | ScaleUp orquesta memoria sin exponer infraestructura. |
| 7 | S22.7 — Validación E2E, privacidad y release | M | Matriz cliente, backup/restore, regresiones y docs verdes. |

## Acceptance Criteria

- [ ] Una instalación limpia contiene el runtime de memoria esperado en cada
  plataforma soportada y no instala datos de empresa compartidos globalmente.
- [ ] La migración se puede repetir y conserva todos los artefactos actuales.
- [ ] La conversación nueva recupera información relevante verificable desde la
  base, aun sin historial de chat.
- [ ] Hechos y decisiones muestran su fuente; las inferencias no confirmadas se
  distinguen o se descartan.
- [ ] Cambios, contradicciones y confianza siguen una política documentada.
- [ ] Fallo o ausencia de SQLite degrada con seguridad al flujo actual.
- [ ] Instalar → conversar → cerrar → abrir sesión nueva → recuperar pasa en
  Claude Code y Codex; Hermes obtiene cobertura equivalente o un límite explícito.
- [ ] Suite completa, smoke real, backup/restore y desinstalación pasan antes del
  cierre.

## Gates Before Implementation

- [ ] ADR aprobado: ubicación de base, esquema, confirmación y retención.
- [ ] Política de migración/rollback aprobada con fixture de empresa existente.
- [ ] Contrato de memoria y casos adversariales escritos antes de tocar el front
  door.
- [x] Diagnóstico RaiSE M documentado localmente el 2026-08-26.
- [x] Base actual: 404 passed, 2 skipped (2026-08-24).
